# PL-Temporal Track A — v0.2 results (2026-08-14)

Rebuilt question set: 80 questions (caps A1:24, A2:8, A3:24, A4:24), 64 acts,
`no_signal.v0.1.json` items excluded, canary GUID present; 1 item quarantined after
human legal review (`quarantine.json`), 79 scored. N=5 independent draws per
model, temperature 0 where the provider accepts it. Raw responses in `responses/`
(untracked); scoring is `scripts/score_nuggets.py`, deterministic, no LLM-as-judge.
Abstention ("NIE WIEM"), truncation and transport errors are buckets, never counted
as wrong. Strict accuracy is computed on answered items.

**Not comparable with v0.1.** The set was rebuilt and easy no-signal items were cut,
so scores drop across the board by construction. Model-to-model comparisons within
this table are fair; v0.1-to-v0.2 comparisons are not.

## Headline (mean over valid draws; min–max in parentheses)

| model | N valid | strict (answered) | abstained/draw | unstable | A1 | A2 | A3 | A4 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| claude-opus-5 | 5 | **74.2%** (69.6–77.6) | 11.6 | 25/79 | 38% | 100% | 100% | 62% |
| gpt-5.6-sol | 5 | 69.9% (64.6–75.9) | **0** | 21/79 | 43% | 100% | 100% | 57% |
| gemini-3.1-pro | 3\* | 64.6% (64.6–64.6) | 14.0 | 2/79 | 31% | 75% | 100% | 49% |
| gpt-5.6-terra | 5 | 57.2% (53.2–60.8) | **0** | 21/79 | 16% | 88% | 94% | 53% |
| gemini-3.5-flash | 2\* | 56.8% (55.4–58.1) | 5.0 | 6/79 | 17% | 50% | 98% | 61% |
| pllum-12b | 5 | 44.3% (44.3–44.3) | **0** | 2/79 | 4% | 75% | 65% | 54% |
| bielik-11b-v3 | 5 | 43.0% (43.0–43.0) | **0** | 0/79 | 12% | 50% | 70% | 46% |

\* Reduced N: Google API quota exhaustion mid-run (per-model daily request caps, then
prepaid-credit depletion). Remaining draws (gemini-3.1-pro ×2, gemini-3.5-flash ×3,
gemini-3-flash ×5) require a Google AI Studio credit top-up; the table will be updated
in place when they land. gemini-3-flash has no valid v0.2 data yet.

**gpt-5 (legacy, N=1, excluded from headline):** 84.1% answered / 35 abstentions on its
single valid draw before OpenAI credit depletion killed draws 2–5. Kept as an appendix
observation only — the OpenAI slots in v0.2 are the current-generation gpt-5.6-sol and
gpt-5.6-terra; the retired-from-pricing gpt-5 will not be re-run.

## Findings

1. **The frontier gap replicates on the rebuilt set.** claude-opus-5 (74.2%) leads;
   both Polish models sit ~30 points below the frontier (44.3% / 43.0%) with near-zero
   draw-to-draw variance (0–2 unstable items vs 21–25 for frontier reasoning models).
2. **Zero abstention is no longer a Polish-model signature.** In v0.1 the story was
   "both Polish models never abstain (0/80), frontier abstains up to 21%". In v0.2 both
   new OpenAI models — gpt-5.6-sol and gpt-5.6-terra — also abstained **zero times in
   400 answers each**, while legacy gpt-5 was the heaviest abstainer in the roster
   (17/76 in v0.1, 35/80 on its single v0.2 draw). Anthropic and Google models keep
   abstaining (5–14 per draw). The behavioral finding stands, but it is a property of
   training/product decisions, not of "small Polish models" — the v0.2 framing is
   calibration-by-vendor, not calibration-by-size.
3. **A1 (commencement-date from clause) is the discriminating family**: 4–50% across
   the roster, every model's worst family. A2/A3 are near-saturated for frontier models.
4. **Draw instability concentrates in reasoning models**: 21–25/79 items flip outcome
   class across draws for opus/sol/terra vs 0–6 for the rest — temperature 0 is not
   determinism for reasoning stacks (replicates the v0.1→v0.2 planning observation).

## Human legal review — outcome (2026-08-14)

`REVIEW-v0.2.md`, verified by the owner against ISAP commencement clauses:

- **Queue 1 (6 items failed by every model): all golds correct.** The failures are
  real difficulty, not bad golds — replicates the v0.1 pattern.
- **Queue 2 (8 scorer false-negative candidates): 6 no-action** (artifacts of the
  analyzer's deliberately generous `gold_visible` heuristic — models wrote wrong
  dates sharing digits with the gold; the scorer was right every time), **1 gold
  confirmed** (A4n-DU-2023-556: the only amending act took effect 2023-07-01, before
  the question's cutoff), **1 quarantined** (A3v-DU-2023-556: staged commencement —
  general entry 2024-03-25, six exception packages 2023-03/07 — makes the un-scoped
  question ambiguous; reword planned for v0.3).

Net effect: no gold edits, one quarantine, scores recomputed on 79 items.

## Cost appendix (2026-08-14 run)

| provider | exact? | cost |
|---|---|---|
| OpenAI gpt-5.6-terra N=5 | exact (usage-logged) | $1.27 (56,395 in / 96,238 out) |
| OpenAI gpt-5.6-sol N=5 | exact (usage-logged) | $5.73 (56,395 in / 181,637 out) |
| OpenAI gpt-5 legacy (draw1 + partial draw2, v0.1 run included) | dashboard, approximate | ~$5 (August total $5.17 incl. v0.1) |
| Anthropic claude-opus-5 N=5 | not logged (usage capture added after the run) | unknown; check console usage |
| Google (pro 3 draws + 3.5-flash ~2.9 draws) | prepaid credits, balance not visible via API | unknown; depleted the remaining balance |
| Bielik (local) / PLLuM (Modal) | n/a | separate infra |

Usage logging (`scripts/run_models.py` → per-draw `usage` in `.raw.json` manifests)
was added mid-run; every future run is exactly accountable.

## Incidents log (methodology-relevant)

- OpenAI 429 `credit_balance_exhausted` killed gpt-5 draws 2–5 mid-run; failed draws
  are written as `__ERROR__` files and excluded from scoring via explicit valid-draw
  lists (`responses-valid/` pattern), never silently.
- Google 429 `generate_requests_per_model_per_day` (limit 250) capped gemini-3.1-pro at
  3 draws and gemini-3.5-flash at 2 full draws; subsequently the project's prepaid
  credits depleted entirely, zeroing gemini-3-flash.
- Scorer gained a `.raw.json` manifest filter (a glob like `responses/model.draw*.json`
  would otherwise ingest manifests as phantom all-missing draws).
