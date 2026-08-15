"""Deterministic scorer. No LLM-as-judge - a judge model carries the same temporal
bias the benchmark measures, and would mark a current-law answer correct.

Usage: python scripts/score_nuggets.py responses.json
       python scripts/score_nuggets.py responses/model.draw*.json
       responses.json = {"<qid>": "<model answer text>", ...}

Multiple files are treated as draws of the SAME model: each is scored alone,
then an aggregate reports mean/min/max strict accuracy and the items whose
outcome class (correct / wrong / abstained / ...) is not stable across draws -
temperature 0 does not make every provider deterministic, so instability is a
measured property of the run, not noise to average away silently.
"""
import json, re, sys, unicodedata
from collections import defaultdict

def norm(s):
    s = unicodedata.normalize("NFKC", s or "")
    s = s.replace(" ", " ").replace("‑", "-").replace("–", "-")
    return re.sub(r"\s+", " ", s).strip()

def num_hits(text):
    return [float(m.replace(",", ".")) for m in re.findall(r"-?\d+(?:[.,]\d+)?", text)]

def hit(ng, resp):
    r = norm(resp)
    k = ng["kind"]
    if k == "regex":      return re.search(ng["pattern"], r, re.I) is not None
    if k == "exact":      return norm(ng["value"]).lower() in r.lower()
    if k == "numeric_tol":
        return any(abs(v - ng["target"]) <= ng["tol"] for v in num_hits(r))
    raise ValueError(f"unknown nugget kind {k}")

def load_quarantine():
    """qids excluded from scoring, each with a recorded reason (quarantine.json).

    Items are quarantined, never deleted: a silently missing question is an
    invisible decision, a quarantined one carries its evidence."""
    try:
        return {x["qid"] for x in json.load(open("quarantine.json"))}
    except FileNotFoundError:
        return set()


def bucket_of(resp):
    r = norm(resp)
    if r.startswith("__ERROR__"):
        return "error"
    if r.startswith("__TRUNCATED__"):
        return "truncated"
    if not r:
        return "empty"
    if re.search(r"\bNIE WIEM\b", r, re.I):
        return "abstained"
    return None


def load_set():
    Q = {q["qid"]: q for q in json.load(open("questions.json"))
         if q.get("qid") != "_CANARY_"}
    quarantined = load_quarantine()
    Q = {qid: q for qid, q in Q.items() if qid not in quarantined}
    NG = defaultdict(list)
    for n in json.load(open("nuggets.json")):
        NG[n["qid"]].append(n)
    return Q, NG, quarantined


def score_one(path, Q, NG):
    """-> (stats dict, outcome-class per qid). Outcome classes: correct / wrong /
    abstained / truncated / error / empty / missing."""
    R = json.load(open(path))
    per_regime = defaultdict(lambda: [0, 0])
    strict_hits = cov_num = cov_den = 0
    missing, buckets = [], defaultdict(list)
    outcome = {}
    # Abstention, truncation and transport error are NOT wrong answers. Counting
    # them as such conflates "the model declined" with "the model was wrong" and
    # inflates every failure rate. Reported as their own buckets (LLHB ruling #29
    # does the same for unverifiable quotes).
    for qid, q in Q.items():
        if qid not in R:
            missing.append(qid); outcome[qid] = "missing"; continue
        b = bucket_of(R[qid])
        if b:
            buckets[b].append(qid); outcome[qid] = b
            continue
        ngs = NG[qid]
        hits = [hit(n, R[qid]) for n in ngs]
        cov_num += sum(hits); cov_den += len(hits)
        strict = all(h for h, n in zip(hits, ngs) if n.get("required", True))
        strict_hits += strict
        outcome[qid] = "correct" if strict else "wrong"
        per_regime[q["regime"]][0] += strict
        per_regime[q["regime"]][1] += 1
    n = len(Q) - len(missing) - sum(len(v) for v in buckets.values())
    return {"path": path, "n": n, "strict": strict_hits, "cov": (cov_num, cov_den),
            "per_regime": per_regime, "buckets": buckets, "missing": missing}, outcome


def report_one(st, total):
    print(f"scored {st['n']}/{total} questions"
          + (f"  (MISSING {len(st['missing'])})" if st["missing"] else ""))
    # Three metrics, three questions (no single headline without a utility function):
    #   coverage          - on what fraction of questions does the model commit to an answer
    #   strict accuracy   - selective precision: how often is it right WHEN it answers
    #   end-to-end acc    - usefulness if the user needs an answer to every question
    print(f"coverage        : {st['n']}/{total} = {100*st['n']/max(total,1):.1f}%")
    print(f"strict accuracy : {st['strict']}/{st['n']} = {100*st['strict']/max(st['n'],1):.1f}%  (on answered)")
    print(f"end-to-end acc  : {st['strict']}/{total} = {100*st['strict']/max(total,1):.1f}%  (abstentions/errors count against)")
    cn, cd = st["cov"]
    print(f"nugget coverage : {cn}/{cd} = {100*cn/max(cd,1):.1f}%")
    for r in sorted(st["per_regime"]):
        h, t = st["per_regime"][r]
        print(f"  {r}: {h}/{t} = {100*h/max(t,1):.1f}%")
    if st["buckets"]:
        print("\nnot scored (never counted as wrong):")
        for k in sorted(st["buckets"]):
            v = st["buckets"][k]
            print(f"  {k:10s} {len(v):3d}  e.g. {', '.join(v[:3])}")
    if st["missing"]:
        m = st["missing"]
        print("\nmissing qids:", ", ".join(m[:10]), "..." if len(m) > 10 else "")


def main(paths):
    # .raw.json files are run manifests, not response maps - a glob like
    # responses/model.draw*.json would otherwise pull them in as phantom draws
    # where every qid scores "missing".
    paths = [p for p in paths if not str(p).endswith(".raw.json")]
    Q, NG, quarantined = load_set()
    if quarantined:
        print(f"quarantined (excluded, see quarantine.json): {len(quarantined)}")
    results = []
    for path in paths:
        st, outcome = score_one(path, Q, NG)
        results.append((st, outcome))
        if len(paths) > 1:
            print(f"\n=== {path} ===")
        report_one(st, len(Q))
    if len(paths) < 2:
        return
    accs = [100 * st["strict"] / max(st["n"], 1) for st, _ in results]
    e2e = [100 * st["strict"] / max(len(Q), 1) for st, _ in results]
    cov = [100 * st["n"] / max(len(Q), 1) for st, _ in results]
    print(f"\n=== aggregate over {len(paths)} draws ===")
    print(f"coverage        : mean {sum(cov)/len(cov):.1f}%  "
          f"min {min(cov):.1f}%  max {max(cov):.1f}%")
    print(f"strict accuracy : mean {sum(accs)/len(accs):.1f}%  "
          f"min {min(accs):.1f}%  max {max(accs):.1f}%  (on answered)")
    print(f"end-to-end acc  : mean {sum(e2e)/len(e2e):.1f}%  "
          f"min {min(e2e):.1f}%  max {max(e2e):.1f}%")
    abst = [len(st["buckets"].get("abstained", [])) for st, _ in results]
    print(f"abstained       : mean {sum(abst)/len(abst):.1f}  "
          f"min {min(abst)}  max {max(abst)}")
    flips = {qid for qid in Q
             if len({o[qid] for _, o in results}) > 1}
    print(f"unstable items  : {len(flips)}/{len(Q)} change outcome class across draws")
    for qid in sorted(flips):
        classes = [o[qid] for _, o in results]
        print(f"  [{Q[qid]['regime']}] {qid}: {' / '.join(classes)}")

if __name__ == "__main__":
    main(sys.argv[1:] if len(sys.argv) > 1 else ["responses.json"])
