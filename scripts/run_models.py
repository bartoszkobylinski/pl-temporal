"""Run the question set against any OpenAI-compatible chat endpoint.

Every model in the roster is described by one entry in models.json:

  {"name": "gpt-x", "base_url": "https://api.openai.com/v1",
   "model": "gpt-x", "api_key_env": "OPENAI_API_KEY",
   "reasoning": "none"}          <- recorded in the output, MUST be reported

Local/self-hosted models (Bielik, PLLuM via vLLM / Ollama / any gateway) need no key:
  {"name": "bielik-11b", "base_url": "http://localhost:11434/v1",
   "model": "SpeakLeash/bielik-11b-v2.6-instruct", "api_key_env": null,
   "reasoning": "none"}

Writes responses/<name>.json = {"<qid>": "<raw answer text>"} plus a run manifest.
Temperature is pinned to 0 where the provider accepts it. Some models reject the
parameter outright (claude-opus-5: "`temperature` is deprecated for this model"), so it
is per-model opt-out via "temperature": null and the manifest records what was actually
sent - an unset sampling control is a fact about the run, not a detail to bury.

--draws N runs the whole set N times per model and writes
responses/<name>.draw<k>.json (k = 1..N). Temperature 0 does NOT make every
provider deterministic (measured on Gemini: 2 of 3 draws identical), so a
single draw is one sample, not "the" answer - v0.2 reports across draws.
With --draws 1 (default) the old flat <name>.json naming is kept.

Answers are stored RAW - no cleaning, no extraction - so the deterministic scorer stays
the only thing that interprets them.
"""
import json, os, sys, re, time, urllib.request, urllib.error

SYSTEM = ("Jesteś asystentem prawniczym. Odpowiadasz na pytania o polskie akty prawne. "
          "Odpowiadaj krótko i konkretnie, w żądanym formacie. "
          "Jeśli nie znasz odpowiedzi, napisz NIE WIEM.")

def _anthropic(cfg, key, prompt, retries):
    """Anthropic Messages API - not OpenAI-compatible, so it gets its own path."""
    body = {"model": cfg["model"], "max_tokens": cfg.get("max_tokens", 4096),
            "system": SYSTEM, "messages": [{"role": "user", "content": prompt}]}
    if cfg.get("temperature") is not None:
        body["temperature"] = cfg["temperature"]
    hdr = {"Content-Type": "application/json", "x-api-key": key,
           "anthropic-version": "2023-06-01", "User-Agent": "pl-temporal-bench/0.1"}
    for i in range(retries):
        try:
            req = urllib.request.Request(cfg["base_url"].rstrip("/") + "/messages",
                                         data=json.dumps(body).encode(), headers=hdr)
            with urllib.request.urlopen(req, timeout=180) as r:
                out = json.load(r)
            text = "".join(b.get("text", "") for b in out.get("content", [])
                           if b.get("type") == "text")
            if not text.strip():
                # A reasoning model can spend the whole budget in its thinking
                # block: stop_reason=max_tokens, zero text blocks. Storing "" here
                # would silently become a wrong answer at scoring time.
                return f"__TRUNCATED__ stop_reason={out.get('stop_reason')} " \
                       f"out_tokens={out.get('usage', {}).get('output_tokens')}"
            return text
        except Exception as e:
            if i == retries - 1:
                return f"__ERROR__ {e}"
            time.sleep(2 * (i + 1))


# accumulated across the run; main() snapshots it per draw so each raw manifest
# carries the draw's exact token spend (needed for per-model cost accounting)
USAGE = {"prompt_tokens": 0, "completion_tokens": 0, "reasoning_tokens": 0}


def chat(cfg, prompt, retries=3):
    key = os.environ.get(cfg["api_key_env"]) if cfg.get("api_key_env") else None
    if cfg.get("api_key_env") and not key:
        raise SystemExit(f"missing env {cfg['api_key_env']} for {cfg['name']}")
    if cfg.get("api") == "anthropic":
        return _anthropic(cfg, key, prompt, retries)
    tok_param = cfg.get("max_tokens_param", "max_tokens")
    body = {"model": cfg["model"], tok_param: cfg.get("max_tokens", 4096),
            "messages": [{"role": "system", "content": SYSTEM},
                         {"role": "user", "content": prompt}]}
    if cfg.get("temperature") is not None:
        body["temperature"] = cfg["temperature"]
    if cfg.get("extra_body"):
        body.update(cfg["extra_body"])
    data = json.dumps(body).encode()
    hdr = {"Content-Type": "application/json", "User-Agent": "pl-temporal-bench/0.1"}
    if key: hdr["Authorization"] = f"Bearer {key}"
    for i in range(retries):
        try:
            req = urllib.request.Request(cfg["base_url"].rstrip("/") + "/chat/completions",
                                         data=data, headers=hdr)
            with urllib.request.urlopen(req, timeout=180) as r:
                out = json.load(r)
            u = out.get("usage") or {}
            USAGE["prompt_tokens"] += u.get("prompt_tokens", 0)
            USAGE["completion_tokens"] += u.get("completion_tokens", 0)
            USAGE["reasoning_tokens"] += (u.get("completion_tokens_details") or {}).get("reasoning_tokens", 0)
            return out["choices"][0]["message"]["content"]
        except urllib.error.HTTPError as e:
            if e.code == 429 and i < retries - 1:
                wait = float(e.headers.get("Retry-After") or 0) or min(60, 5 * 2**i)
                time.sleep(wait)
                continue
            if i == retries - 1:
                return f"__ERROR__ HTTP {e.code}"
            time.sleep(2 * (i + 1))
        except Exception as e:
            if i == retries - 1:
                return f"__ERROR__ {e}"
            time.sleep(2 * (i + 1))

def strip_thinking(text):
    """Reasoning models emit <think>…</think> before the answer. Strip it BEFORE
    scoring, or a stray 'NIE' inside the reasoning trace scores a false hit."""
    return re.sub(r"<think>.*?</think>", " ", text or "", flags=re.S | re.I).strip()

def main():
    args = sys.argv[1:]
    draws = 1
    if "--draws" in args:
        i = args.index("--draws")
        draws = int(args[i + 1])
        del args[i:i + 2]
    # the canary record is not a question - sending it to a model would defeat it
    Q = [q for q in json.load(open("questions.json")) if q.get("qid") != "_CANARY_"]
    roster = json.load(open(args[0] if args else "models.json"))
    os.makedirs("responses", exist_ok=True)
    for cfg in roster:
        name = cfg["name"]
        pace = float(cfg.get("pace_seconds", 0))
        for k in range(1, draws + 1):
            stem = name if draws == 1 else f"{name}.draw{k}"
            out, raw = {}, {}
            u0 = dict(USAGE)
            print(f"--- {stem} ({len(Q)} questions) ---")
            for i, q in enumerate(Q, 1):
                if pace and i > 1:
                    time.sleep(pace)
                ans = chat(cfg, q["prompt"])
                raw[q["qid"]] = ans
                out[q["qid"]] = strip_thinking(ans)
                if i % 10 == 0: print(f"    {i}/{len(Q)}")
            du = {k2: USAGE[k2] - u0[k2] for k2 in USAGE}
            json.dump(out, open(f"responses/{stem}.json", "w"), ensure_ascii=False, indent=1)
            json.dump({"model": cfg, "n": len(Q), "draw": k, "draws": draws, "usage": du,
                       "raw": raw},
                      open(f"responses/{stem}.raw.json", "w"), ensure_ascii=False, indent=1)
            errs = sum(1 for v in out.values() if v.startswith("__ERROR__"))
            print(f"    wrote responses/{stem}.json" + (f"  ({errs} ERRORS)" if errs else ""))
            print(f"    usage: in={du['prompt_tokens']} out={du['completion_tokens']} "
                  f"(reasoning {du['reasoning_tokens']})")

if __name__ == "__main__":
    main()
