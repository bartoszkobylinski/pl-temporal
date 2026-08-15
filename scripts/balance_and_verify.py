"""Balance the generated set, then RE-DERIVE every gold answer from the live API
with code that shares nothing with the generator. A mismatch fails the build.

v0.2: caps shift weight to the discriminating families (A1 hard for the whole
roster, A3v title-proof, A4 carries the post-cutoff staleness probes); items the
entire v0.1 roster answered correctly (no_signal.v0.1.json) are excluded up
front; A2 recency and its recheck run on `promulgation` (Dz.U. publication),
not announcementDate; the leading _CANARY_ record passes through untouched."""
import json, random, urllib.request, sys, re
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor

BASE="https://api.sejm.gov.pl/eli"; TODAY="2026-08-12"; SEED=42
CAPS={"A1":24,"A2":8,"A3":24,"A4":24}

def api(eli):
    p,y,n=eli.split("/")
    r=urllib.request.Request(f"{BASE}/acts/{p}/{y}/{n}",
        headers={"Accept":"application/json","User-Agent":"pl-temporal-verify/0.2"})
    return json.load(urllib.request.urlopen(r,timeout=60))

raw=json.load(open("questions.json")); N=json.load(open("nuggets.json"))
canary=[q for q in raw if q.get("qid")=="_CANARY_"]
Q=[q for q in raw if q.get("qid")!="_CANARY_"]
random.seed(SEED)

def normqid(qid): return re.sub(r"-\d{4}-\d{2}-\d{2}$","",qid)
try:
    ns=set(json.load(open("no_signal.v0.1.json"))["qids"])
    before=len(Q)
    Q=[q for q in Q if normqid(q["qid"]) not in ns]
    print(f"no-signal exclusion: {before-len(Q)} items dropped ({len(ns)} listed)")
except FileNotFoundError:
    pass

# ---- balance: keep vacatio A3 first (the discriminating shape), then balance answers
buckets=defaultdict(list)
for q in Q: buckets[q["regime"]].append(q)
keep=[]
for r,cap in CAPS.items():
    items=buckets[r]
    if r=="A3":
        vac=[q for q in items if q["qid"].startswith("A3v-")]
        rest=[q for q in items if not q["qid"].startswith("A3v-")]
        random.shuffle(vac); random.shuffle(rest)
        yes=[q for q in rest if q["gold"]["canonical_answer"]=="TAK"]
        no =[q for q in rest if q["gold"]["canonical_answer"]=="NIE"]
        take=vac[:cap]                      # v0.2: every vacatio item carried signal - take all
        half=(cap-len(take))//2
        take+=yes[:half]+no[:cap-len(take)-half]
        keep+=take
    elif r=="A4":
        yes=[q for q in items if q["gold"]["canonical_answer"]=="TAK"]
        no =[q for q in items if q["gold"]["canonical_answer"]=="NIE"]
        random.shuffle(yes); random.shuffle(no)
        k=min(len(no),cap//2)
        keep+=no[:k]+yes[:cap-k]
    else:
        random.shuffle(items)
        if r=="A1":
            # The three A1 items v0.1 quarantined for staged commencement come
            # back DELIBERATELY (their disposition: "reformulate in v0.2") -
            # they are the regression probes for the generator's carve-out
            # handling, so their inclusion must not depend on the shuffle.
            try:
                pri={x["qid"] for x in json.load(open("quarantine.v0.1.json"))
                     if x["qid"].startswith("A1-")}
                items=[q for q in items if q["qid"] in pri]+[q for q in items if q["qid"] not in pri]
            except FileNotFoundError:
                pass
        keep+=items[:cap]

kept={q["qid"] for q in keep}

# ---- independent re-derivation
def recheck(q):
    eli=q["gold"]["act_eli"]; a=api(eli); g=q["gold"]["canonical_answer"]; r=q["regime"]
    anc=q["date_anchor"]
    if r=="A1":
        return a.get("entryIntoForce")==g, f"api={a.get('entryIntoForce')}"
    if r=="A2":
        tj=(a.get("references") or {}).get("Inf. o tekście jednolitym",[]) or []
        best=None
        for t in tj:                       # resolve ALL, no truncation
            p,y,n=t["id"].split("/"); c=api(t["id"])
            pd=c.get("promulgation") or c.get("announcementDate")
            if pd and pd<=anc and (best is None or pd>best[0]): best=(pd,int(y),int(n))
        exp=f"Dz.U. {best[1]} poz. {best[2]}" if best else None
        return exp==g, f"recomputed={exp}"
    if r=="A3":
        eif=a.get("entryIntoForce")
        exp="TAK" if (eif and anc>=eif) else "NIE"
        return exp==g, f"entryIntoForce={eif}"
    if r=="A4":
        ams=[e["date"] for e in ((a.get("references") or {}).get("Akty zmieniające",[]) or [])
             if e.get("date")]
        exp="TAK" if any(x>anc for x in ams) else "NIE"
        return exp==g, f"edges_after_anchor={sum(1 for x in ams if x>anc)}/{len(ams)}"
    return False,"unknown regime"

print(f"verifying {len(keep)} items against the live API (independent derivation)...")
bad=[]
with ThreadPoolExecutor(max_workers=4) as ex:
    for q,(ok,note) in zip(keep, ex.map(recheck, keep)):
        if not ok: bad.append((q["qid"], q["regime"], q["gold"]["canonical_answer"], note))

print(f"\nMISMATCHES: {len(bad)}")
for b in bad: print("   ", b)
if bad:
    print("\nrefusing to write a set with unverified gold answers", file=sys.stderr)
    sys.exit(1)

json.dump(canary+keep, open("questions.json","w"), ensure_ascii=False, indent=1)
json.dump([n for n in N if n["qid"] in kept], open("nuggets.json","w"), ensure_ascii=False, indent=1)
print("\nfinal set:", len(keep), dict(Counter(q["regime"] for q in keep)))
print("answers  :", dict(Counter(q["gold"]["canonical_answer"] for q in keep
                                 if q["regime"] in ("A3","A4"))))
print("acts     :", len({q["gold"]["act_eli"] for q in keep}))
