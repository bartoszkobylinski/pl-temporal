# Incident report: analyzer scored abstentions as answers (2026-08-15)

## Bug

`analyze_failures.py` fed every present response straight into the nugget matcher.
The scorer (`score_nuggets.py`) buckets abstention ("NIE WIEM"), truncation and
transport errors BEFORE matching; the analyzer did not. Consequence: for questions
with gold `NIE` (regex `\bNIE\b`), an abstained answer "NIE WIEM" matched the
nugget and was labeled a correct answer. Reported by an external reviewer;
confirmed same day.

**Scope: diagnostic labels only.** Headline results were never affected — the
scorer has always had the correct bucketing, and all published accuracy numbers
come from the scorer.

## Forensic method

Old rule (no bucket filter) vs new rule (scorer buckets excluded) computed on
identical inputs (`analysis/forensic_analyzer_diff.py`, full output in
`forensic-output-2026-08-15.txt`):

1. v0.2 valid draws (31 run files, 79 questions) — do current diagnostic labels change?
2. v0.1 responses (7 models, 76 questions, the run that produced
   `no_signal.v0.1.json`) — did the bug shape the v0.2 item selection?

## Findings

| measure | v0.2 runs | v0.1 run |
|---|---:|---:|
| bug instances (bucketed answer labeled correct) | 39 | 9 |
| `all_wrong` (review Queue 1) old → new | 6 → 6 (unchanged) | 9 → 9 (unchanged) |
| `all_right` (no-signal candidates) old → new | 14 → 15 | 33 → 34 |

Every bug instance is the predicted class: family A4n, gold `NIE`, answer
"NIE WIEM" (models: gemini-3.1-pro, gpt-5, claude-opus-5, gemini-3.5-flash,
gemini-3-flash).

**No-signal cut audit (the question that matters):** all 33 items in the published
`no_signal.v0.1.json` remain answered-correctly-by-every-model under the fixed
analyzer — **zero items were wrongly cut**. The implementation bug affected
diagnostic labels but did not affect the selected v0.2 item set.

**One footnote:** `A3y-DU-2023-1450` is all-right under the fixed analyzer but was
NOT cut (under the old rule one abstention with gold `TAK` blocked its all-right
status). v0.2 therefore contains one item that the corrected no-signal rule would
have removed — a uniformly easy item for every model, no ranking distortion;
scheduled for removal in the v1.0 frozen set.

## Fix

`analyze_failures.py` now imports `bucket_of` from the scorer and excludes bucketed
responses from all correctness labels; `all_right` additionally requires every model
to have actually answered (a bucketed response blocks no-signal status — an
abstention is signal). Section 3 (`gold_visible`) considers answered-and-wrong
responses only. Regenerated analysis: `failures-v0.2-fixed.txt`.

## Implications

- Review queues (REVIEW-v0.2.md) built on the old analyzer stand: Queue 1 identical;
  Queue 2 rows were owner-adjudicated per item and none of the adjudications relied
  on a bucketed answer.
- v1.0 selection procedure will be pre-registered and run only on the fixed analyzer.
