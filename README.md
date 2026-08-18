# PL-Temporal — Track A (Diagnostic Challenge Set v0.2)

A diagnostic challenge set for closed-book temporal QA over Polish statutes: which
version of the law was in force on a given date, when did an act enter into force,
which Dziennik Ustaw position is the current consolidated text. 80 questions across 64 acts, 4 question
families, deterministic string-nugget scoring — no LLM-as-judge.

> **Status: v0.2 frozen as a diagnostic challenge set.** Because no-signal items were
> pruned using v0.1 model results, v0.2 measures model discrimination on hard items,
> not accuracy on a representative sample — a frozen v1.0 with a pre-registered
> selection procedure is planned. All analyzer-flagged golds were verified by the
> dataset owner against ISAP commencement clauses (zero gold edits, one ambiguous
> item quarantined; an independent second annotation pass is planned for v1.0).
> See `REVIEW-v0.2.md`, `RESULTS-v0.2.md` (limitations) and
> `analysis/analyzer-abstention-incident.md`.

## Question families

| family | n | what it tests |
|---|---:|---|
| A1 | 24 | commencement date of an act, derived from its commencement clause |
| A2 | 8 | which Dz.U. position is the consolidated text (tekst jednolity) in force on a date |
| A3 | 24 | whether an act was in force on a given date (TAK/NIE) |
| A4 | 24 | whether an act was amended in a given period (TAK/NIE) |

Abstention ("NIE WIEM"), truncation, and transport errors are separate buckets, never
counted as wrong. Strict accuracy is computed on answered items.

## v0.2 results (79 scored items; mean over valid draws)

Three metrics, three questions — there is no single leader without a utility
function. *Coverage*: how often the model answers at all. *Selective accuracy*: how
often it is right when it answers. *End-to-end*: usefulness when every question
needs an answer.

| model | N | coverage | selective acc | end-to-end | abstained/draw |
|---|---:|---:|---:|---:|---:|
| gpt-5.6-sol | 5 | **100%** | 69.9% | **69.9%** | **0** |
| claude-opus-5 | 5 | 85.1% | **74.2%** | 63.0% | 11.6 |
| gpt-5.6-terra | 5 | 100% | 57.2% | 57.2% | **0** |
| gemini-3.1-pro | 3 | 82.3% | 64.6% | 53.2% | 14.0 |
| gemini-3.5-flash | 2 | 93.7% | 56.8% | 53.2% | 5.0 |
| pllum-12b | 5 | 100% | 44.3% | 44.3% | **0** |
| bielik-11b-v3 | 5 | 100% | 43.0% | 43.0% | **0** |

Majority baselines for the binary families: A3 = 65.2%, A4 = 50.0%.

Full tables, findings, per-family accuracy, cost accounting, and incident log:
`RESULTS-v0.2.md`. Notable: zero-abstention is a property of vendor training decisions,
not of model size — both GPT-5.6 models abstained 0/400, matching the Polish models,
while legacy gpt-5 was the heaviest abstainer in the roster.

## Running

```bash
# roster file: see models.example.json (any OpenAI-compatible chat endpoint + Anthropic)
python3 scripts/run_models.py models.json --draws 5   # writes responses/<model>.drawK.json
python3 scripts/score_nuggets.py responses/<model>.draw*.json
python3 scripts/analyze_failures.py responses
```

The committed analysis under `analysis/` was produced over the **31 valid draws** listed in
`valid-draws-v0.2.json`, not over everything in `responses/` — draws killed by provider
quota exhaustion are shipped for transparency but excluded from scoring. Running the command
above over the whole directory picks up 45 draws and will not reproduce the committed
numbers; filter to the valid draws first.

The runner logs exact per-draw token usage into `responses/*.raw.json` manifests.
Scoring is deterministic: normalized string-nugget matching (`scripts/score_nuggets.py`),
one implementation shared by the scorer and the analyzer.

## Contamination canary

`questions.json` contains a `_CANARY_` record with a unique GUID that is not a question
and is never sent to models by the runner. If a model can reproduce this GUID, this
dataset was in its training data — please report such a finding as an issue. Note the
asymmetry: reproducing the GUID is positive evidence of contamination, but failing to
reproduce it does not prove the absence of contamination.

## Data provenance and legal basis

Source of legal texts and metadata: Internetowy System Aktów Prawnych (ISAP),
Kancelaria Sejmu RP — https://isap.sejm.gov.pl — and the Sejm ELI API —
https://api.sejm.gov.pl / https://eli.gov.pl. Retrieved: 2026-08-12/13 (dataset build dates). The texts have been processed (fragment
extraction, paraphrase, derived dates); they are informational only and are not a
source of law. Authentic texts are solely those promulgated in Dziennik Ustaw /
Monitor Polski. This benchmark is not legal advice; answers reflect the law as
retrieved on the stated date.

Statute texts are excluded from copyright under art. 4 of the Polish Copyright Act
(ustawa z 4.02.1994 o prawie autorskim i prawach pokrewnych) and are in the public
domain; the CC BY 4.0 license applies to the compilation, questions, nuggets, and
metadata. See `LICENSE`.

## Citation

See `CITATION.cff`. Paper: in preparation.
