# PL-Temporal — Track A

A benchmark of temporal legal reasoning over Polish statutes: which version of the law
was in force on a given date, when did an act enter into force, which Dziennik Ustaw
position is the current consolidated text. 80 questions across 64 acts, 4 question
families, deterministic string-nugget scoring — no LLM-as-judge.

> **Status: pre-release skeleton.** Gold answers are undergoing independent human legal
> review (`REVIEW-v0.2.md`); do not treat scores as final until this notice is removed.

## Question families

| family | n | what it tests |
|---|---:|---|
| A1 | 24 | commencement date of an act, derived from its commencement clause |
| A2 | 8 | which Dz.U. position is the consolidated text (tekst jednolity) in force on a date |
| A3 | 24 | whether an act was in force on a given date (TAK/NIE) |
| A4 | 24 | whether an act was amended in a given period (TAK/NIE) |

Abstention ("NIE WIEM"), truncation, and transport errors are separate buckets, never
counted as wrong. Strict accuracy is computed on answered items.

## v0.2 results (2026-08-14, N=5 draws where provider quotas allowed)

| model | N valid | strict (answered) | abstained/draw |
|---|---:|---:|---:|
| claude-opus-5 | 5 | **73.1%** (68.6–76.5) | 11.6 |
| gpt-5.6-sol | 5 | 69.8% (65.0–75.0) | **0** |
| gemini-3.1-pro | 3 | 63.6% | 14.0 |
| gpt-5.6-terra | 5 | 57.2% (52.5–61.2) | **0** |
| gemini-3.5-flash | 2 | 56.0% (54.7–57.3) | 5.0 |
| pllum-12b | 5 | 43.8% | **0** |
| bielik-11b-v3 | 5 | 42.5% | **0** |

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

The runner logs exact per-draw token usage into `responses/*.raw.json` manifests.
Scoring is deterministic: normalized string-nugget matching (`scripts/score_nuggets.py`),
one implementation shared by the scorer and the analyzer.

## Contamination canary

`questions.json` contains a `_CANARY_` record with a unique GUID that is not a question
and is never sent to models by the runner. If a model can reproduce this GUID, this
dataset was in its training data — please report such a finding as an issue.

## Data provenance and legal basis

Source of legal texts and metadata: Internetowy System Aktów Prawnych (ISAP),
Kancelaria Sejmu RP — https://isap.sejm.gov.pl — and the Sejm ELI API —
https://api.sejm.gov.pl / https://eli.gov.pl. Retrieved: 2026-08 (exact per-release
retrieval date: TODO before publication). The texts have been processed (fragment
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
