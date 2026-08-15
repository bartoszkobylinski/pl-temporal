"""Audit whether substring-nugget scoring could have credited ambiguous answers.

Counts, over every ANSWERED (non-bucketed) response in the valid v0.2 draws:
  - A1: answers containing more than one distinct ISO date
        (subset: gold date present AND another date present - the risky class)
  - A2: answers containing more than one distinct Dz.U. position candidate
  - A3/A4: answers containing both TAK and NIE as standalone words
  - all families: answers longer than 120 chars (extra reasoning around the answer)

Usage: python3 analysis/strictness_audit.py [responses_dir]  (default responses-valid)
"""
import json, re, sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
from score_nuggets import norm, bucket_of

def main(rdir="responses-valid"):
    Q = {q["qid"]: q for q in json.load(open("questions.json")) if q.get("qid") != "_CANARY_"}
    try:
        quar = {x["qid"] for x in json.load(open("quarantine.json"))}
        Q = {k: v for k, v in Q.items() if k not in quar}
    except FileNotFoundError:
        pass
    stats = defaultdict(int)
    examples = defaultdict(list)
    answered = 0
    for p in sorted(Path(rdir).glob("*.json")):
        if p.name.endswith(".raw.json"):
            continue
        R = json.load(open(p))
        for qid, q in Q.items():
            ans = R.get(qid)
            if ans is None or bucket_of(ans):
                continue
            answered += 1
            a = norm(ans)
            fam = q["regime"]
            if len(a) > 120:
                stats["long_answers"] += 1
            if fam == "A1":
                dates = set(re.findall(r"\b\d{4}-\d{2}-\d{2}\b", a))
                if len(dates) > 1:
                    stats["A1_multi_date"] += 1
                    examples["A1_multi_date"].append((qid, p.stem, a[:90]))
                    gold = str(q["gold"].get("canonical_answer", ""))
                    if gold in dates:
                        stats["A1_multi_date_incl_gold"] += 1
                        examples["A1_multi_date_incl_gold"].append((qid, p.stem, a[:90]))
            elif fam == "A2":
                poss = set(re.findall(r"poz\.?\s*(\d+)", a, re.I))
                if len(poss) > 1:
                    stats["A2_multi_position"] += 1
                    examples["A2_multi_position"].append((qid, p.stem, a[:90]))
            elif fam in ("A3", "A4"):
                has_tak = re.search(r"\bTAK\b", a, re.I)
                has_nie = re.search(r"\bNIE\b", a, re.I)
                if has_tak and has_nie:
                    stats["A3A4_both_tak_nie"] += 1
                    examples["A3A4_both_tak_nie"].append((qid, p.stem, a[:90]))
    print(f"answered responses audited: {answered} "
          f"(runs in {rdir}/, {len(Q)} questions)")
    for k in ("A1_multi_date", "A1_multi_date_incl_gold", "A2_multi_position",
              "A3A4_both_tak_nie", "long_answers"):
        print(f"{k:26s}: {stats[k]}")
    for k, rows in examples.items():
        print(f"\n--- {k} ---")
        for qid, m, a in rows[:10]:
            print(f"  {qid} / {m}: {a}")

if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "responses-valid")
