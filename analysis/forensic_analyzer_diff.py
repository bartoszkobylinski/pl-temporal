"""Forensic diff: analyzer correctness labels OLD rule (no abstention/error
filtering) vs NEW rule (scorer buckets excluded), on v0.1 and v0.2 responses.
Answers two questions:
  Q1: does the bug change current v0.2 diagnostic labels?
  Q2: did the bug affect the v0.1 no-signal cut that shaped the v0.2 item set?
"""
import json, re, sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from score_nuggets import hit, norm, bucket_of

BASE = Path(__file__).resolve().parent
REPO = Path("/Users/bartoszkobylinski/Programming/Python/lovspor-notebook/benchmarks/pl-temporal")


def load_set(qpath, ngpath, quarpath):
    Q = {q["qid"]: q for q in json.load(open(qpath)) if q.get("qid") != "_CANARY_"}
    try:
        quar = {x["qid"] for x in json.load(open(quarpath))}
    except FileNotFoundError:
        quar = set()
    Q = {k: v for k, v in Q.items() if k not in quar}
    NG = defaultdict(list)
    for n in json.load(open(ngpath)):
        NG[n["qid"]].append(n)
    return Q, NG


def load_runs(rdir):
    runs = {}
    for p in sorted(Path(rdir).glob("*.json")):
        if p.name.endswith(".raw.json"):
            continue
        runs[p.stem] = json.load(open(p))
    return runs


def labels(Q, NG, runs, new_rule):
    """-> correct[qid][model] bool over ANSWERED-only (new) or ALL-present (old);
    plus bug_instances: (qid, model, bucket) where old would call hit() on a
    bucketed answer."""
    correct = defaultdict(dict)
    bugs = []
    for qid, q in Q.items():
        for m, R in runs.items():
            ans = R.get(qid)
            if ans is None:
                continue
            b = bucket_of(ans)
            ok = all(hit(n, ans) for n in NG[qid] if n.get("required", True))
            if b:
                if ok:  # bucketed answer the old matcher scores as correct = bug firing
                    bugs.append((qid, m, b))
                if new_rule:
                    continue  # new rule: bucketed answers never enter correct{}
            correct[qid][m] = ok
    return correct, bugs


def sets(Q, correct, n_models, require_full=False):
    all_wrong = [q for q in Q if correct[q] and not any(correct[q].values())]
    if require_full:
        all_right = [q for q in Q if len(correct[q]) == n_models and all(correct[q].values())]
    else:
        all_right = [q for q in Q if correct[q] and all(correct[q].values())]
    return set(all_wrong), set(all_right)


def strip_anchor(qid):
    return re.sub(r"-\d{4}-\d{2}-\d{2}$", "", qid)


def report(tag, Q, NG, runs):
    n_models = len(runs)
    old_c, bugs = labels(Q, NG, runs, new_rule=False)
    new_c, _ = labels(Q, NG, runs, new_rule=True)
    ow, orr = sets(Q, old_c, n_models)
    nw, nr = sets(Q, new_c, n_models)
    print(f"\n########## {tag} ({n_models} runs, {len(Q)} questions) ##########")
    print(f"bug instances (bucketed answer scored correct by old matcher): {len(bugs)}")
    for qid, m, b in bugs:
        print(f"  {qid} / {m} [{b}]  gold={Q[qid]['gold'].get('canonical_answer')!r}")
    print(f"all_wrong: old {len(ow)} -> new {len(nw)}"
          f"  (+{sorted(nw-ow)}  -{sorted(ow-nw)})")
    print(f"all_right: old {len(orr)} -> new {len(nr)}"
          f"  (+{sorted(nr-orr)}  -{sorted(orr-nr)})")
    return orr, nr


# ---- Q1: v0.2 current labels (responses-valid, current set) ----
Q2, NG2 = load_set(REPO/"questions.json", REPO/"nuggets.json", REPO/"quarantine.json")
runs2 = load_runs(REPO/"responses-valid")
report("v0.2 / responses-valid", Q2, NG2, runs2)

# ---- Q2: v0.1 no-signal cut provenance ----
Q1, NG1 = load_set(BASE/"v01/questions.json", BASE/"v01/nuggets.json", BASE/"v01/quarantine.json")
runs1 = load_runs(REPO/"responses-v0.1")
orr1, nr1 = report("v0.1 / responses-v0.1", Q1, NG1, runs1)

cut = json.load(open(REPO/"no_signal.v0.1.json"))["qids"]
cut_set = set(cut)
old_stripped = {strip_anchor(q) for q in orr1}
new_stripped = {strip_anchor(q) for q in nr1}
print(f"\n########## no-signal cut audit ##########")
print(f"published cut list: {len(cut_set)} qids (anchor-stripped rule)")
print(f"old-analyzer all_right (stripped): {len(old_stripped)}")
print(f"new-analyzer all_right (stripped): {len(new_stripped)}")
wrongly_cut = sorted(cut_set - new_stripped)
would_now_cut = sorted(new_stripped - cut_set)
print(f"WRONGLY CUT (in published cut, NOT all-right under fixed analyzer): {len(wrongly_cut)}")
for q in wrongly_cut:
    print(f"  {q}")
print(f"would-now-cut (all-right under fixed analyzer, not in published cut): {len(would_now_cut)}")
for q in would_now_cut:
    print(f"  {q}")
