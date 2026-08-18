# PL-Temporal v0.2 — human legal review sheet

Sorted by analyzer signal (`analysis/failures-v0.2.txt`, generated from valid draws
only). Two queues; work top-down. For each item: check the gold against the act's
commencement clause (przepis końcowy) in ISAP, mark VERDICT gold-ok / gold-wrong /
question-ambiguous, and note the evidence (Dz.U. + article).

## Queue 1 — failed by EVERY model (6 items; bad gold or ambiguous prompt until proven otherwise)

*Label note (2026-08-15): "every model" here is the lenient, per-draw rule in force when this
queue was built. Under the symmetric full-coverage rule the queue is empty — each of these six
items has at least one abstention among the 31 draws. The review below stands as extra
verification; see `analysis/analyzer-abstention-incident.md` § Hardening follow-up.*

| # | qid | gold | verdict | evidence |
|---|---|---|---|---|
| 1 | A1-DU-2001-1408 | 2002-11-10 | gold-ok | ISAP przepis koncowy, verified by owner 2026-08-14 |
| 2 | A1-DU-2012-1091 | 2012-10-17 | gold-ok | ISAP przepis koncowy, verified by owner 2026-08-14 |
| 3 | A1-DU-2021-904 | 2021-05-15 | gold-ok | ISAP przepis koncowy, verified by owner 2026-08-14 |
| 4 | A1-DU-2006-874 | 2006-07-29 | gold-ok | ISAP przepis koncowy, verified by owner 2026-08-14 |
| 5 | A1-DU-2006-1533 | 2006-12-06 | gold-ok | ISAP przepis koncowy, verified by owner 2026-08-14 |
| 6 | A1-DU-2014-1071 | 2014-08-26 | gold-ok | ISAP przepis koncowy, verified by owner 2026-08-14 |

Note on #1: models cluster on three different dates (2003-01-01 ×3 draws opus,
2002-05-17 ×3 gemini-pro, 2002-02-10 ×4 sol) — disagreement pattern suggests a
non-trivial commencement clause (vacatio legis staged?), verify the clause directly.

## Queue 2 — scorer false-negative candidates (gold string visible, nugget said FAIL)

Sorted by hit count across valid draws. These change scores WITHOUT touching models —
check whether the nugget is too strict, not whether the model is right.

| # | qid | hits | suspicion |
|---|---|---:|---|
| 1 | A1-DU-2007-328 | 19 | no-action: models wrote wrong dates (2007-04-01/15); digit-overlap artifact of gold_visible |
| 2 | A1-DU-2004-624 | 13 | no-action: wrong dates (2004-05-01, 16.07, 16.04); same artifact |
| 3 | A2-DU-2006-1539-2014-10-05 | 5 | no-action: bielik cites poz. 1446 vs gold 144; substring artifact, scorer right |
| 4 | A1-DU-2021-904 | 5 | no-action: wrong dates (2021-05-20, 16.05); gold-ok per Queue 1 |
| 5 | A3v-DU-2023-556 | 4 | RESOLVED 2026-08-14: quarantined (question-ambiguous; staged commencement — general entry 2024-03-25 vs exception packages 2023-03/07; evidence in quarantine.json) |
| 6 | A1-DU-2004-2784 | 3 | no-action: terra wrote 2005-01-15/12/14; digit artifact |
| 7 | A4n-DU-2023-556 | 1 | RESOLVED 2026-08-14: gold-ok (sole amending act Dz.U. 2023 poz. 1059 effective 2023-07-01, before the cutoff; ISAP, verified by owner) |
| 8 | A2-DU-2001-353-2016-01-27 | 1 | no-action: "poz. 1030" vs gold "poz. 103"; model wrong, matcher artifact |

## Cut candidates (no signal)

14 items answered correctly by every model — list in `analysis/failures-v0.2.txt`
section 2. Candidates for pruning in v0.3, not for review.
