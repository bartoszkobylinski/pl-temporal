# PL-Temporal v0.2 — human legal review sheet

Sorted by analyzer signal (`analysis/failures-v0.2.txt`, generated from valid draws
only). Two queues; work top-down. For each item: check the gold against the act's
commencement clause (przepis końcowy) in ISAP, mark VERDICT gold-ok / gold-wrong /
question-ambiguous, and note the evidence (Dz.U. + article).

## Queue 1 — failed by EVERY model (6 items; bad gold or ambiguous prompt until proven otherwise)

| # | qid | gold | verdict | evidence |
|---|---|---|---|---|
| 1 | A1-DU-2001-1408 | 2002-11-10 | | |
| 2 | A1-DU-2012-1091 | (see questions.json) | | |
| 3 | A1-DU-2021-904 | (see questions.json) | | |
| 4 | A1-DU-2006-874 | (see questions.json) | | |
| 5 | A1-DU-2006-1533 | (see questions.json) | | |
| 6 | A1-DU-2014-1071 | (see questions.json) | | |

Note on #1: models cluster on three different dates (2003-01-01 ×3 draws opus,
2002-05-17 ×3 gemini-pro, 2002-02-10 ×4 sol) — disagreement pattern suggests a
non-trivial commencement clause (vacatio legis staged?), verify the clause directly.

## Queue 2 — scorer false-negative candidates (gold string visible, nugget said FAIL)

Sorted by hit count across valid draws. These change scores WITHOUT touching models —
check whether the nugget is too strict, not whether the model is right.

| # | qid | hits | suspicion |
|---|---|---:|---|
| 1 | A1-DU-2007-328 | 19 | nugget format vs date-in-text mismatch |
| 2 | A1-DU-2004-624 | 13 | as above |
| 3 | A2-DU-2006-1539-2014-10-05 | 5 | bielik cites tekst jednolity in prose |
| 4 | A1-DU-2021-904 | 5 | also in Queue 1 — double signal |
| 5 | A3v-DU-2023-556 | 4 | opus consistently answers TAK vs gold NIE — gold suspect |
| 6 | A1-DU-2004-2784 | 3 | |
| 7 | A4n-DU-2023-556 | 1 | same act as #5 — review together |
| 8 | A2-DU-2001-353-2016-01-27 | 1 | "poz. 1030" vs gold "poz. 103" — model wrong, generous
        matcher artifact; likely no action |

## Cut candidates (no signal)

14 items answered correctly by every model — list in `analysis/failures-v0.2.txt`
section 2. Candidates for pruning in v0.3, not for review.
