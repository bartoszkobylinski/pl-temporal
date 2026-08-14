# PL-Temporal Track A — v0.2 results (2026-08-14)

Rebuilt question set: 80 questions (caps A1:24, A2:8, A3:24, A4:24), 64 acts,
`no_signal.v0.1.json` items excluded, canary GUID present. N=5 independent draws per
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
| claude-opus-5 | 5 | **73.1%** (68.6–76.5) | 11.6 | 25/80 | 38% | 100% | 96% | 62% |
| gpt-5.6-sol | 5 | 69.8% (65.0–75.0) | **0** | 22/80 | 43% | 100% | 98% | 57% |
| gemini-3.1-pro | 3\* | 63.6% (63.6–63.6) | 14.0 | 2/80 | 31% | 75% | 96% | 49% |
| gpt-5.6-terra | 5 | 57.2% (52.5–61.2) | **0** | 22/80 | 16% | 88% | 92% | 53% |
| gemini-3.5-flash | 2\* | 56.0% (54.7–57.3) | 5.0 | 6/80 | 17% | 50% | 94% | 61% |
| pllum-12b | 5 | 43.8% (43.8–43.8) | **0** | 2/80 | 4% | 75% | 62% | 54% |
| bielik-11b-v3 | 5 | 42.5% (42.5–42.5) | **0** | 0/80 | 12% | 50% | 67% | 46% |

\* Reduced N: Google API quota exhaustion mid-run (per-model daily request caps, then
prepaid-credit depletion). Remaining draws (gemini-3.1-pro ×2, gemini-3.5-flash ×3,
gemini-3-flash ×5) require a Google AI Studio credit top-up; the table will be updated
in place when they land. gemini-3-flash has no valid v0.2 data yet.

**gpt-5 (legacy, N=1, excluded from headline):** 84.4% answered / 35 abstentions on its
single valid draw before OpenAI credit depletion killed draws 2–5. Kept as an appendix
observation only — the OpenAI slots in v0.2 are the current-generation gpt-5.6-sol and
gpt-5.6-terra; the retired-from-pricing gpt-5 will not be re-run.

## Findings

1. **The frontier gap replicates on the rebuilt set.** claude-opus-5 (73.1%) leads;
   both Polish models sit ~30 points below the frontier (43.8% / 42.5%) with near-zero
   draw-to-draw variance (0–2 unstable items vs 22–25 for frontier reasoning models).
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
4. **Draw instability concentrates in reasoning models**: 22–25/80 items flip outcome
   class across draws for opus/sol/terra vs 0–6 for the rest — temperature 0 is not
   determinism for reasoning stacks (replicates the v0.1→v0.2 planning observation).

## Review queue

`REVIEW-v0.2.md`: 6 items failed by every model (gold/prompt suspects, A1-heavy) and
8 scorer false-negative candidates. Full evidence: `analysis/failures-v0.2.txt`.

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
