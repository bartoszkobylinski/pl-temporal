"""Point the review at the items that need it, instead of at a total.

Reads every responses/<model>.json and asks four questions:

  1. Which items did EVERY model get wrong? An item the whole roster fails the same
     way is usually a bad gold answer or an ambiguous prompt - not a hard question.
     These are the first candidates for human legal review.
  2. Which items did EVERY model get right? Carries no signal; candidates for cutting.
  3. Where did the scorer say FAIL while the gold string is visibly present in the
     answer? That is a scorer false negative - the nugget is too strict, not the model
     wrong. Fixing these changes scores without touching any model.
  4. How does each family behave, per model?

Usage: python scripts/analyze_failures.py [responses_dir]
"""
import json, re, sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from score_nuggets import hit, norm, bucket_of  # one scoring implementation, never two


def load(responses_dir):
    # multi-draw runs (<model>.draw<k>.json) appear as separate columns; for
    # "failed/answered by EVERY model" that is the conservative reading - one
    # unstable draw is enough to keep an item.
    Q = {q["qid"]: q for q in json.load(open("questions.json"))
         if q.get("qid") != "_CANARY_"}
    try:
        quarantined = {x["qid"] for x in json.load(open("quarantine.json"))}
        Q = {qid: q for qid, q in Q.items() if qid not in quarantined}
    except FileNotFoundError:
        pass
    NG = defaultdict(list)
    for n in json.load(open("nuggets.json")):
        NG[n["qid"]].append(n)
    runs = {}
    for p in sorted(Path(responses_dir).glob("*.json")):
        if p.name.endswith(".raw.json"):
            continue
        runs[p.stem] = json.load(open(p))
    return Q, NG, runs


def gold_visible(q, answer):
    """Cheap, deliberately generous check that the gold is in the text at all."""
    g = norm(str(q["gold"].get("canonical_answer", ""))).lower()
    a = norm(answer or "").lower()
    if not g:
        return False
    if g in a:
        return True
    nums = re.findall(r"\d+", g)
    return bool(nums) and all(re.search(rf"\b{n}\b", a) for n in nums)


def main(responses_dir="responses"):
    Q, NG, runs = load(responses_dir)
    if not runs:
        print(f"no responses in {responses_dir}/"); return
    models = sorted(runs)
    print(f"models: {', '.join(models)}   questions: {len(Q)}\n")

    correct = defaultdict(dict)   # qid -> model -> bool, ANSWERED responses only
    bucketed = defaultdict(dict)  # qid -> model -> bucket (abstained/error/...)
    for qid, q in Q.items():
        for m in models:
            ans = runs[m].get(qid)
            if ans is None:
                continue
            # The scorer buckets abstention/truncation/error BEFORE nugget matching;
            # the analyzer must do the same, or "NIE WIEM" matches a gold-NIE regex
            # and an abstention is counted as a correct answer (bug found 2026-08-15;
            # forensic diff in analysis/analyzer-abstention-incident.md).
            b = bucket_of(ans)
            if b:
                bucketed[qid][m] = b
                continue
            ngs = NG[qid]
            correct[qid][m] = all(hit(n, ans) for n in ngs if n.get("required", True))

    # Both labels require EVERY model to have actually answered (not abstained,
    # not errored): an abstention is neither a failure nor a success, so an item
    # with any bucketed response is neither "failed by every model" nor a
    # no-signal cut candidate - a bucketed response is signal, not noise.
    all_wrong = [qid for qid in Q
                 if len(correct[qid]) == len(models) and not any(correct[qid].values())]
    all_right = [qid for qid in Q
                 if len(correct[qid]) == len(models) and all(correct[qid].values())]
    n_bucketed = sum(len(v) for v in bucketed.values())
    if n_bucketed:
        print(f"(bucketed responses excluded from correctness labels: {n_bucketed})\n")

    print(f"=== 1. failed by EVERY model: {len(all_wrong)} — review these first ===")
    for qid in all_wrong:
        q = Q[qid]
        print(f"  [{q['regime']}] {qid}")
        print(f"      gold: {q['gold'].get('canonical_answer')}")
        for m in models:
            a = norm(runs[m].get(qid, ""))[:88]
            print(f"      {m:17s}: {a}")

    print(f"\n=== 2. answered by EVERY model: {len(all_right)} — no signal, cut candidates ===")
    by_reg = defaultdict(int)
    for qid in all_right:
        by_reg[Q[qid]["regime"]] += 1
    print("  ", dict(by_reg) or "(none)")

    print("\n=== 3. scorer false negatives (gold visible, nugget says FAIL) ===")
    fn = 0
    for qid, q in Q.items():
        for m in models:
            ans = runs[m].get(qid)
            # bucketed answers are not scorer failures - only answered-and-wrong count
            if ans and m in correct[qid] and not correct[qid][m] and gold_visible(q, ans):
                fn += 1
                print(f"  [{q['regime']}] {qid} / {m}")
                print(f"      gold: {q['gold'].get('canonical_answer')}")
                print(f"      said: {norm(ans)[:88]}")
    if not fn:
        print("  (none — nuggets are not obviously too strict)")

    print("\n=== 4. per-family accuracy ===")
    hdr = f"  {'family':8s}" + "".join(f"{m:>19s}" for m in models)
    print(hdr)
    for reg in sorted({q["regime"] for q in Q.values()}):
        qs = [qid for qid, q in Q.items() if q["regime"] == reg]
        row = f"  {reg:8s}"
        for m in models:
            hits = sum(1 for qid in qs if correct[qid].get(m))
            tot = sum(1 for qid in qs if m in correct[qid])
            row += f"{hits:>10d}/{tot:<3d}{100*hits/max(tot,1):>5.0f}%"
        print(row)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "responses")
