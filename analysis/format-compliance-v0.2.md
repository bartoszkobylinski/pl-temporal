# Format compliance vs semantic correctness on v0.2 (2026-09-02)

## What this measures and why it did not exist before

`score_nuggets.py` credits a required nugget found **anywhere** in the response. So

```
2007-04-04
Ustawa weszła w życie dnia 4 kwietnia 2007 r., czyli 2007-04-04.
```

score identically, even though the prompt asked for the date *in the format RRRR-MM-DD*.
Semantic correctness and compliance with the requested form are therefore one number in
the published v0.2 results, and nothing in the artifact says which of the two a model
failed at.

`scripts/score_protocol.py` separates them **without touching the frozen artifact**. Golds,
nuggets and the draw selection in `valid-draws-v0.2.json` are read as-is; semantic accuracy
is computed by the same rule `score_nuggets.py` uses and must reproduce the published
figures exactly. `--self-check` fails if it does not, and CI runs it (`tests/`).

Requested forms are the ones the prompts state: A1 `RRRR-MM-DD`, A2 `Dz.U. rok poz. numer`,
A3/A4 `TAK` albo `NIE`.

## Results

```
python scripts/score_protocol.py --self-check     # the table below, plus the v0.2 reproduction
python scripts/score_protocol.py --audit          # the per-family and overlap numbers quoted below
```

| model | N | abstention | bare (answered) | bare (correct) | leading (correct) | semantic acc (answered) | protocol acc | v0.2 end-to-end |
|---|---|---|---|---|---|---|---|---|
| gpt-5.6-sol | 5 | 0.0% | 100.0% | 100.0% | 100.0% | 69.9% | 69.9% | 69.9% |
| gpt-5.6-terra | 5 | 0.0% | 100.0% | 100.0% | 100.0% | 57.2% | 57.2% | 57.2% |
| gemini-3.1-pro | 3 | 17.7% | 100.0% | 100.0% | 100.0% | 64.6% | 53.2% | 53.2% |
| gemini-3.5-flash | 2 | 6.3% | 100.0% | 100.0% | 100.0% | 56.8% | 53.2% | 53.2% |
| gpt-5 | 1 | 44.3% | 100.0% | 100.0% | 100.0% | 84.1% | 46.8% | 46.8% |
| pllum-12b | 5 | 0.0% | 74.7% | 100.0% | 100.0% | 44.3% | 44.3% | 44.3% |
| bielik-11b-v3 | 5 | 0.0% | 62.0% | 79.4% | 79.4% | 43.0% | 34.2% | 43.0% |
| claude-opus-5 | 5 | 14.7% | 43.5% | 40.5% | 100.0% | 74.2% | 25.6% | 63.0% |

Column definitions:

- **bare** — the whole answer is the requested form and nothing else (markdown bold,
  surrounding quotes and a trailing full stop are stripped first; they do not change the
  value).
- **leading** — the answer *opens* with the requested form, prose may follow.
- **(answered)** conditions on the model having answered; **(correct)** conditions on the
  answer also being semantically right.
- **protocol acc** — bare **and** correct *within the bare span*, over all 79 items.
- **v0.2 end-to-end** — the published figure, reproduced.

## Findings

**1. No published v0.2 figure is inflated by lenient matching.** Every semantic accuracy
reproduces to within 0.05pp. Whatever else is below, it is an *addition* to the results, not
a correction of them.

**2. Conditioning matters more than the metric.** PLLuM's format compliance reads 74.7% over
all answered and **100%** over correct answers: its off-format responses are Polish prose
dates ("Ustawa weszła w życie 13 stycznia 2002 r."), which also miss the exact date nugget
and were therefore *already counted wrong*. Reporting them again as format failures would
double-count one error. The `(correct)` column is the one that measures a separate axis;
the `(answered)` column mostly re-measures wrongness. **Report both or neither.**

**3. Only two models deviate once the condition is applied, and for opposite reasons.**

- `bielik-11b-v3` — **79.4%** bare among its correct answers: roughly one correct answer in
  five arrives in a form the prompt did not ask for. Per family, its bare-format rate over
  all answered is A1 8%, A2 0%, A3 100%, A4 100% (`--audit`) — binary questions are answered
  in form, derived values are not.
- `claude-opus-5` — **40.5%** bare but **100%** leading. It always emits the correct value
  first and then explains (`**2008-03-22** Ustawa (Dz.U. 2008 nr 39, poz. 226) weszła w
  życie…`). This is not a compliance failure in any sense that matters to a consumer of the
  answer; it is why `leading` is published beside `bare` instead of `bare` alone.

**4. The strict reading is an interpretation, and it is labelled as one.** The prompts ask
for the answer in a given form; they do not say "and write nothing else". `bare` is the
right rule for a machine-consumed protocol and the wrong rule to publish alone — the gap
between `bare` and `leading` (40.5% → 100% for claude-opus-5 over its correct answers) is
the size of that interpretation, so both are reported.

**5. Protocol accuracy reorders the table.** Under `protocol acc`, claude-opus-5 falls from
63.0% (2nd) to 25.6% (last) and bielik from 43.0% to 34.2%, while the OpenAI pair is
unmoved. A single "how good is this model" number was never available here — v0.2 already
said that — and the protocol column makes the reason concrete rather than abstract.

## The ordering invariant, pinned

Abstention is classified **before** any answer parsing. For the 28 items whose gold nugget
is `\bNIE\b`, the abstention phrase `NIE WIEM` satisfies the gold: **39 of 145
abstention-bucketed responses would score as correct** if the parser ran first
(`--audit`; over the valid draws, quarantined item excluded). `score_nuggets.py` is safe only because `bucket_of()` precedes nugget matching in
`score_one()`; `analyze_failures.py` shipped without that order and produced exactly this
error (see `analyzer-abstention-incident.md`).

The order is now a test (`tests/test_score_protocol.py`), not a convention.

## Abstention detection, checked

`bucket_of()` recognises abstention by the literal `NIE WIEM` — the phrase the system prompt
requests. Tested hypothesis: this under-counts models that decline in other words, which
would make the "zero abstention is a vendor-training property" finding an artifact of the
detector.

**It does not.** Probing nine soft-abstention patterns (`nie mam pewności`, `brak danych`,
`nie jestem w stanie`, `nie potrafię`, `nie dysponuję`, …) across the 2,448 responses in the
valid draws finds **three** declines outside the detector, all from `claude-opus-5`. Bielik
and PLLuM produce zero of either kind in 395 answers each (`--audit`). The pattern list is
hand-built and bounds the effect rather than proving it is zero.

## What this does not do

- It does not change v0.2. The frozen files, their checksums and the published numbers are
  untouched.
- It does not introduce provider-native structured output. Constrained decoding differs per
  provider (Bielik and PLLuM run through a plain OpenAI-compatible endpoint), so enabling it
  would make the roster incomparable — and comparability of Polish models against frontier
  models is the headline finding. Any future protocol must be defined and parsed here, once,
  for every model.
- It does not change the prompts. A prompt-level protocol requires a rerun and belongs to
  v1.0.
