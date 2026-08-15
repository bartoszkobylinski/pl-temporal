# PL-Temporal Diagnostic Challenge Set — v0.2 results (2026-08-14, revised 2026-08-15)

Rebuilt question set: 80 questions (caps A1:24, A2:8, A3:24, A4:24), 64 acts,
`no_signal.v0.1.json` items excluded, canary GUID present; 1 item quarantined after
human legal review (`quarantine.json`), 79 scored. N=5 independent draws per
model, temperature 0 where the provider accepts it. Raw responses in `responses/`
(untracked in the notebook; published in the public repo); scoring is
`scripts/score_nuggets.py`, deterministic, no LLM-as-judge. Abstention ("NIE WIEM"),
truncation and transport errors are separate categories, never counted as wrong.

**v0.2 is FROZEN as a historical diagnostic run.** Because items with no model
signal were pruned using v0.1 model results, this set measures model discrimination
on hard items, not accuracy on a representative sample of Polish statutory
questions — hence "Diagnostic Challenge Set", not "benchmark". A frozen v1.0 with a
pre-registered selection procedure (no model-informed pruning of the test split) is
the planned citable artifact. Known v0.2 limitations are listed at the bottom; none
of them will be patched in place — fixes land in v1.0 with a full roster re-run.

**Not comparable with v0.1.** The set was rebuilt and easy no-signal items were cut,
so scores drop across the board by construction. Model-to-model comparisons within
this table are fair; v0.1-to-v0.2 comparisons are not.

## Headline — three metrics, three questions (mean over valid draws; min–max)

No single leader exists without a utility function. *Coverage* asks how often the
model commits to an answer; *selective accuracy* asks how often it is right when it
answers; *end-to-end accuracy* asks how useful it is if every question needs an
answer. A user who requires an answer to every question should read the end-to-end
column (gpt-5.6-sol leads); a user for whom a wrong legal answer is much costlier
than a refusal should read selective accuracy (claude-opus-5 leads at 85% coverage).

| model | N valid | coverage | selective acc (answered) | end-to-end acc | abst./draw | unstable |
|---|---:|---:|---:|---:|---:|---:|
| gpt-5.6-sol | 5 | **100%** | 69.9% (64.6–75.9) | **69.9%** (64.6–75.9) | **0** | 21/79 |
| claude-opus-5 | 5 | 85.1% (82.3–87.3) | **74.2%** (69.6–77.6) | 63.0% (60.8–65.8) | 11.6 | 25/79 |
| gpt-5.6-terra | 5 | **100%** | 57.2% (53.2–60.8) | 57.2% (53.2–60.8) | **0** | 21/79 |
| gemini-3.1-pro | 3\* | 82.3% | 64.6% | 53.2% | 14.0 | 2/79 |
| gemini-3.5-flash | 2\* | 93.7% | 56.8% (55.4–58.1) | 53.2% (51.9–54.4) | 5.0 | 6/79 |
| pllum-12b | 5 | **100%** | 44.3% | 44.3% | **0** | 2/79 |
| bielik-11b-v3 | 5 | **100%** | 43.0% | 43.0% | **0** | 0/79 |

Per-family selective accuracy (answered): A1 — opus 38 / sol 43 / gpro 31 / terra 16 /
g35 17 / pllum 4 / bielik 12%; A2 — 100/100/75/88/50/75/50%; A3 — 100/100/100/94/98/65/70%;
A4 — 62/57/49/53/61/54/46%. **Majority baselines for the binary families: A3 = 65.2%**
(15×NIE / 8×TAK — a model at ~65% on A3 is at the trivial baseline; pllum-12b's 65% is
exactly that), **A4 = 50.0%** (12/12, balanced). The 8 A3n items (query date before
enactment) are answerable without any legal knowledge and act as a sanity control —
v1.0 will report them separately from the core temporal score.

\* Reduced N: Google API quota exhaustion mid-run (per-model daily request caps, then
prepaid-credit depletion). Remaining draws (gemini-3.1-pro ×2, gemini-3.5-flash ×3,
gemini-3-flash ×5) require a Google AI Studio credit top-up; the table will be updated
in place when they land. gemini-3-flash has no valid v0.2 data yet.

**gpt-5 (legacy, N=1, excluded from headline):** coverage 55.7%, selective 84.1%,
end-to-end 46.8% (35 abstentions on its single valid draw before OpenAI credit
depletion killed draws 2–5). The starkest illustration of the coverage/precision
trade-off in the roster; kept as an appendix observation only — the OpenAI slots in
v0.2 are the current-generation gpt-5.6-sol and gpt-5.6-terra.

## Findings

1. **There is no single leader — the coverage/precision trade-off is the result.**
   gpt-5.6-sol wins end-to-end (69.9%) by answering everything; claude-opus-5 wins
   selective accuracy (74.2%) at 85% coverage. Which model is "better" depends on
   the cost of a wrong legal answer versus the cost of a refusal. Reporting a single
   accuracy-on-answered number (as v0.2 did until 2026-08-15) hides this: it made
   opus look like the outright leader while a full-coverage model beat it end-to-end.
2. **Zero abstention is a vendor-training property, not a size property.** Both
   Polish models AND both new OpenAI models (gpt-5.6-sol, gpt-5.6-terra) abstained
   zero times in 400 answers each, while legacy gpt-5 was the heaviest abstainer in
   the roster (17/76 in v0.1, 35/80 on its single v0.2 draw). Anthropic and Google
   models abstain 5–14 per draw. The v0.1 framing "small Polish models never say
   I-don't-know" is dead; the correct framing is calibration-by-vendor.
3. **The frontier gap replicates on the rebuilt set** on every metric: both Polish
   models sit ~26 pp below the best end-to-end model and ~30 pp below the best
   selective model, with near-zero draw-to-draw variance (0–2 unstable items vs
   21–25 for frontier reasoners).
4. **A1 (commencement-date from clause) is the discriminating family**: 4–43%
   selective accuracy across the roster, every model's worst family. A3 is partly
   saturated AND partly trivial (majority baseline 65.2%; A3n sanity items) — v1.0
   restructures it into core-vs-control.
5. **Draw instability concentrates in reasoning models**: 21–25/79 items flip
   outcome class across draws for opus/sol/terra vs 0–6 for the rest — temperature 0
   is not determinism for reasoning stacks.

## Human legal review — outcome (2026-08-14)

`REVIEW-v0.2.md`, all analyzer-flagged items verified **by the dataset owner**
against ISAP commencement clauses (a second, independent annotator over all 79 golds
is planned before v1.0; per-item evidence metadata — evidence article, derivation
type, retrieval date — will make the set self-auditing):

- **Queue 1 (6 items failed by every model): all golds correct.** The failures are
  real difficulty, not bad golds — replicates the v0.1 pattern.
- **Queue 2 (8 scorer false-negative candidates): 6 no-action** (artifacts of the
  analyzer's deliberately generous `gold_visible` heuristic), **1 gold confirmed**
  (A4n-DU-2023-556), **1 quarantined** (A3v-DU-2023-556: staged commencement —
  general entry 2024-03-25, six exception packages 2023-03/07 — makes the un-scoped
  question ambiguous; the quarantined pattern seeds the "staged commencement" hard
  class in v1.0).

Net effect: no gold edits, one quarantine, scores computed on 79 items.

## Analyzer incident (2026-08-15)

An external review found that `analyze_failures.py` fed abstentions into the nugget
matcher ("NIE WIEM" matched gold-`NIE` regexes). Headline results were never
affected (the scorer always bucketed correctly). Forensic diff over v0.1 and v0.2
runs: 39+9 mislabeled diagnostic instances, review queues unchanged, and **zero
items wrongly cut** from the v0.2 set; one item (A3y-DU-2023-1450) would
additionally have been cut and remains as a uniformly-easy item. Full report:
`analysis/analyzer-abstention-incident.md`. Fixed the same day.

## Strictness audit (2026-08-15)

Could substring nuggets credit ambiguous answers ("considered X, but correct is Y")?
Audit over all 2,303 answered responses: **zero** A1 multi-date answers, **zero**
false credits in the 24 verbose A2 answers, one benign TAK+"nie"-in-prose case.
The matcher is empirically sufficient for this run; deterministic answer extraction
is planned for v1.0 as defense-in-depth. Full audit:
`analysis/strictness-audit-v0.2.md`.

## Known v0.2 limitations (frozen; fixes land in v1.0)

1. **A4 has no right time boundary** ("amended with effect after X?" — as of when?).
   Negative golds are correct as of the dataset build date (2026-08-12/13) but can
   flip as new amendments pass. v1.0 bounds every A4 question to an explicit window
   ("in the period X to 2026-08-12").
2. **A3n items are trivially answerable** (query date before enactment); reported
   here inside A3, separated into a sanity control in v1.0, which also adds hard
   negatives (published-but-not-yet-in-force; staged commencement).
3. **Model-informed pruning**: the no-signal cut used v0.1 model results, so v0.2 is
   a diagnostic/discrimination set, not a representative sample. v1.0 freezes a
   pre-registered selection procedure.
4. **One leftover no-signal item** (A3y-DU-2023-1450, see analyzer incident) —
   uniformly easy, no ranking effect.
5. **Single annotator** for the gold review (owner); independent second pass planned.
6. **Min–max ranges are draw ranges, not confidence intervals**; hierarchical
   (act-level, draw-aware) bootstrap planned for the paper.

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
- Analyzer abstention bug (2026-08-15) — see the incident section above.
