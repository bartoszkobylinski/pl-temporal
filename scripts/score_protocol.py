"""Four-metric scorer: abstention, format compliance, semantic accuracy, protocol accuracy.

`score_nuggets.py` credits a nugget found ANYWHERE in the response, so an answer that
ignores the format the prompt asked for scores exactly like a conforming one. That makes
semantic correctness and format compliance one number, and the published v0.2 results
therefore cannot say which of the two a model failed at.

This script separates them WITHOUT touching the frozen artifact: the golds, the nuggets and
the draw selection are read as-is, and semantic accuracy is computed by the same rule
`score_nuggets.py` uses, so it must reproduce the published figures exactly. It does not
re-derive a single gold - `--self-check` fails loudly if the reproduction drifts.

  abstention        - the model declined, per the protocol phrase the system prompt asks for
  format compliance - the answer is the requested form and nothing else (of those answered)
  semantic accuracy - required nuggets satisfied anywhere in the response (v0.2's number)
  protocol accuracy - conforming AND correct within the conforming span, over all items

The requested form per family is the one the prompts themselves state:

  A1  RRRR-MM-DD                     A3  TAK albo NIE
  A2  Dz.U. rok poz. numer           A4  TAK albo NIE

ORDERING INVARIANT: abstention is classified before any answer parsing. For the 28 items
whose gold nugget is `\\bNIE\\b`, the abstention phrase "NIE WIEM" satisfies the gold; a
parser that ran first would score a decline as a correct answer. `score_nuggets.py` is safe
for the same reason, and `analyze_failures.py` was not (RESULTS-v0.2.md:111-119). Keep the
order, and keep the test that pins it.

Usage:
  python scripts/score_protocol.py                  # every model in valid-draws-v0.2.json
  python scripts/score_protocol.py claude-opus-5    # one model
  python scripts/score_protocol.py --self-check     # also verify the v0.2 reproduction
  python scripts/score_protocol.py --audit          # per-family formats + the two overlap
                                                    # measurements quoted in the analysis
"""
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from score_nuggets import bucket_of, hit, load_set, norm  # noqa: E402

# The bare form each family's prompt asks for. Anchored: a conforming answer is the value
# and nothing else, because "and nothing else" is the part v0.2 never measured.
FORMS = {
    "A1": r"\d{4}-\d{2}-\d{2}",
    "A2": r"Dz\.\s*U\.\s*\d{4}\s*poz\.\s*\d+",
    "A3": r"TAK|NIE",
    "A4": r"TAK|NIE",
}

# Decoration a conforming answer may still carry: markdown bold, surrounding quotes, a
# trailing full stop. These do not change the value and no prompt forbids them; stripping
# them keeps "format compliance" a claim about the ANSWER SHAPE, not about markdown.
DECOR = re.compile(r"^[\s*_\"'`]+|[\s*_\"'`.]+$")


def strip_decor(text):
    return DECOR.sub("", norm(text))


def parse_strict(resp, regime):
    """The whole answer is the requested form -> that form. Otherwise None."""
    body = strip_decor(resp)
    m = re.fullmatch(FORMS[regime], body, re.I)
    return m.group(0) if m else None


def parse_leading(resp, regime):
    """The answer OPENS with the requested form, prose may follow -> that form.

    Reported next to the strict rule on purpose. The prompts ask for the answer in a given
    form; they do not say "and write nothing else". Reading them strictly is defensible for
    a machine-consumed protocol and indefensible as the only number, so both are published
    and the gap between them is the size of the interpretation."""
    body = strip_decor(resp)
    m = re.match(FORMS[regime] + r"(?![\w-])", body, re.I)
    return m.group(0) if m else None


def parse_lenient(resp, regime):
    """First occurrence of the requested form anywhere -> that form. Otherwise None."""
    m = re.search(FORMS[regime], norm(resp), re.I)
    return m.group(0) if m else None


def classify(resp, q, ngs):
    """-> (outcome, conforming: bool, semantic_ok: bool).

    Outcomes: abstained / truncated / error / empty (non-answers, never counted wrong),
    else correct / wrong by the v0.2 rule. `conforming` and the protocol verdict are
    reported alongside, never folded into the accuracy the frozen results published.
    """
    non_answer = bucket_of(resp)          # ORDERING INVARIANT - do not move below parsing
    if non_answer:
        return non_answer, False, False
    required = [n for n in ngs if n.get("required", True)]
    semantic_ok = all(hit(n, resp) for n in required)
    span = parse_strict(resp, q["regime"])
    conforming = span is not None
    return ("correct" if semantic_ok else "wrong"), conforming, semantic_ok


def protocol_ok(resp, q, ngs):
    """Conforming AND correct *within the conforming span* - not merely somewhere in the
    prose around it. A model that emits the bare form has nowhere else to hide the answer,
    so this is the metric a structured protocol would produce."""
    span = parse_strict(resp, q["regime"])
    if span is None:
        return False
    return all(hit(n, span) for n in ngs if n.get("required", True))


def score_file(path, Q, NG):
    responses = json.load(open(path))
    stats = {
        "n_items": len(Q), "answered": 0, "abstained": 0, "non_answer": 0,
        "conforming": 0, "leading": 0, "semantic": 0, "protocol": 0, "missing": 0,
        "conforming_correct": 0, "leading_correct": 0,
    }
    for qid, q in Q.items():
        if qid not in responses:
            stats["missing"] += 1
            continue
        resp = responses[qid]
        outcome, conforming, semantic_ok = classify(resp, q, NG[qid])
        if outcome in ("abstained", "truncated", "error", "empty"):
            stats["non_answer"] += 1
            stats["abstained"] += outcome == "abstained"
            continue
        leads = parse_leading(resp, q["regime"]) is not None
        stats["answered"] += 1
        stats["conforming"] += conforming
        stats["leading"] += leads
        stats["semantic"] += semantic_ok
        stats["protocol"] += protocol_ok(resp, q, NG[qid])
        # Conditioned on the answer being RIGHT. Without this condition the format column
        # mostly re-measures wrongness: a model that answers A1 in Polish prose ("13
        # stycznia 2002 r.") fails the exact date nugget too, so it is already counted as
        # wrong, and reporting it again as a format failure would double-count one error.
        if semantic_ok:
            stats["conforming_correct"] += conforming
            stats["leading_correct"] += leads
    return stats


def mean(xs):
    return sum(xs) / len(xs) if xs else 0.0


def valid_draw_paths(model, base="responses"):
    """Draw selection is the frozen one: draws killed by provider quota/credit exhaustion
    are excluded by valid-draws-v0.2.json, not re-judged here."""
    draws = json.load(open("valid-draws-v0.2.json"))["valid_draws"]
    paths = []
    for k in draws.get(model, []):
        per_draw = f"{base}/{model}.draw{k}.json"
        if os.path.exists(per_draw):
            paths.append(per_draw)
            continue
        # run_models.py writes the flat name ONLY under --draws 1, so that file is one
        # draw's answers however many indices the manifest lists for the model. Adding it
        # once per index would report the same responses as several independent draws:
        # the means would not move (identical values) but the draw count, and any min-max
        # taken over them, would be fiction.
        flat = f"{base}/{model}.json"
        if os.path.exists(flat) and flat not in paths:
            paths.append(flat)
    return paths


# Declines phrased in something other than the protocol phrase. Hand-built: it BOUNDS the
# blind spot of the literal "NIE WIEM" detector, it does not prove the blind spot is empty.
SOFT_ABSTENTION = [
    r"nie mam (pewno|dost|informa)", r"nie jestem (pewien|pewna|w stanie)",
    r"brak (danych|informacji)", r"nie potrafi[\u0119e]",
    r"nie mog[\u0119e] (ustali|potwierdzi|poda)", r"nie uda\u0142o si\u0119 ustali\u0107",
    r"nie znam", r"nie dysponuj[\u0119e]", r"trudno (jednoznacznie )?(ustali|stwierdzi)",
]


def audit(Q, NG):
    """The three measurements the analysis quotes, recomputed here so no number in
    analysis/format-compliance-v0.2.md comes from a script that was not committed."""
    draws = json.load(open("valid-draws-v0.2.json"))["valid_draws"]
    print("\n--- per-family bare format, over all answered ---")
    print(f"{'model':18s} " + " ".join(f"{r:>6s}" for r in sorted(FORMS)))
    for model, ks in draws.items():
        if not ks:
            continue
        per = {r: [0, 0] for r in FORMS}
        for path in valid_draw_paths(model):
            responses = json.load(open(path))
            for qid, q in Q.items():
                resp = responses.get(qid)
                if resp is None or bucket_of(resp):
                    continue
                per[q["regime"]][1] += 1
                per[q["regime"]][0] += parse_strict(resp, q["regime"]) is not None
        cells = " ".join(f"{100 * n / d:5.0f}%" if d else "    -" for r in sorted(per)
                         for n, d in [per[r]])
        print(f"{model:18s} {cells}")

    # How much the ordering invariant is actually holding back.
    masked = abstained = 0
    for model in draws:
        for path in valid_draw_paths(model):
            for qid, resp in json.load(open(path)).items():
                if qid not in Q or bucket_of(resp) != "abstained":
                    continue
                abstained += 1
                masked += all(hit(n, resp) for n in NG[qid] if n.get("required", True))
    print(f"\n--- ordering invariant ---\nabstentions that would score CORRECT if the parser "
          f"ran before bucket_of(): {masked}/{abstained}")

    # Whether the literal-phrase detector misses declines phrased differently.
    print("\n--- declines outside the 'NIE WIEM' detector ---")
    for model in draws:
        hard = soft = seen = 0
        for path in valid_draw_paths(model):
            for qid, resp in json.load(open(path)).items():
                if qid not in Q:
                    continue
                r = norm(resp)
                if r.startswith("__"):
                    continue
                seen += 1
                if bucket_of(resp) == "abstained":
                    hard += 1
                elif any(re.search(pat, r, re.I) for pat in SOFT_ABSTENTION):
                    soft += 1
        if seen:
            print(f"{model:18s} NIE WIEM {hard:4d}   soft-only {soft:3d}   n {seen:4d}")


def main(argv):
    self_check = "--self-check" in argv
    wanted = [a for a in argv if not a.startswith("--")]
    Q, NG, quarantined = load_set()
    total = len(Q)
    models = wanted or [m for m, d in json.load(open("valid-draws-v0.2.json"))["valid_draws"].items() if d]

    print(f"{total} scored items ({len(quarantined)} quarantined, excluded)\n")
    rows = []
    for model in models:
        paths = valid_draw_paths(model)
        if not paths:
            print(f"{model}: no valid draws on disk - skipped")
            continue
        per_draw = [score_file(p, Q, NG) for p in paths]
        # Mean of per-draw ratios, NOT ratio of means: RESULTS-v0.2 aggregates that way
        # (score_nuggets.py builds `accs` per draw and averages), and for a model whose
        # coverage moves between draws the two differ - claude-opus-5 by 0.1pp.
        def per_draw_pct(num, den):
            return 100 * mean([s[num] / max(s[den], 1) for s in per_draw])
        row = {
            "model": model,
            "draws": len(per_draw),
            "abstention": 100 * mean([s["abstained"] / total for s in per_draw]),
            "format": per_draw_pct("conforming", "answered"),
            "leading": per_draw_pct("leading", "answered"),
            "format_ok": per_draw_pct("conforming_correct", "semantic"),
            "leading_ok": per_draw_pct("leading_correct", "semantic"),
            "semantic": per_draw_pct("semantic", "answered"),
            "protocol": 100 * mean([s["protocol"] / total for s in per_draw]),
            "e2e_v02": 100 * mean([s["semantic"] / total for s in per_draw]),
        }
        rows.append(row)

    rows.sort(key=lambda r: -r["protocol"])
    print("| model | N | abstention | bare (answered) | bare (correct) | leading (correct) | "
          "semantic acc (answered) | protocol acc | v0.2 end-to-end |")
    print("|---|---|---|---|---|---|---|---|---|")
    for r in rows:
        print(f"| {r['model']} | {r['draws']} | {r['abstention']:.1f}% | {r['format']:.1f}% | "
              f"{r['format_ok']:.1f}% | {r['leading_ok']:.1f}% | {r['semantic']:.1f}% | "
              f"{r['protocol']:.1f}% | {r['e2e_v02']:.1f}% |")

    if "--audit" in argv:
        audit(Q, NG)

    if self_check:
        print("\n--- self-check: semantic accuracy must reproduce RESULTS-v0.2.md ---")
        published = {"gpt-5.6-sol": 69.9, "claude-opus-5": 74.2, "gpt-5.6-terra": 57.2,
                     "gemini-3.1-pro": 64.6, "gemini-3.5-flash": 56.8, "pllum-12b": 44.3,
                     "bielik-11b-v3": 43.0}
        bad = 0
        for r in rows:
            exp = published.get(r["model"])
            if exp is None:
                continue
            delta = abs(r["semantic"] - exp)
            flag = "ok" if delta <= 0.05 else "DRIFT"
            bad += delta > 0.05
            print(f"  {r['model']:18s} recomputed {r['semantic']:5.1f}%  published {exp:5.1f}%  {flag}")
        if bad:
            raise SystemExit(f"{bad} model(s) do not reproduce the published selective accuracy")
        print("  all published figures reproduced")


if __name__ == "__main__":
    main(sys.argv[1:])
