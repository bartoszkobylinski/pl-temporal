# pl-temporal — Roadmap

Last reviewed: 2026-10-17 · Reviewed against: 65f1c43
Product: standalone · Product roadmap: this file

PL-Temporal is a diagnostic challenge set for closed-book temporal QA over Polish
statutes (80 questions, 64 acts, 4 families, deterministic string-nugget scoring;
README.md). v0.2 is frozen (CITATION.cff `version: "0.2"`, `CHECKSUMS-v0.2.txt`);
the last change on `main` is PR #5, merged 2026-09-02, and no PR or branch is open.

## Now
- (none recorded) — no open PRs, no open issues, `main` is the only branch.

## Next
All items below are written down by the owner as v1.0 work ("fixes land in v1.0 with a
full roster re-run", RESULTS-v0.2.md). No work on them is visible in the repository.
- Frozen v1.0 with a pre-registered selection procedure (no model-informed pruning of
  the test split), run only on the fixed analyzer, selection labels at per-model
  (draw-aggregated) granularity — source: README.md (Status); RESULTS-v0.2.md
  (intro, limitation 3); analysis/analyzer-abstention-incident.md (Hardening follow-up, Implications)
- Independent second annotator over all 79 golds — source: README.md (Status);
  RESULTS-v0.2.md (Human legal review; limitation 5)
- Per-item evidence metadata (evidence article, derivation type, retrieval date) —
  source: RESULTS-v0.2.md (Human legal review)
- Deterministic answer extraction + canonical comparison — source: RESULTS-v0.2.md
  (Strictness audit); analysis/strictness-audit-v0.2.md (Conclusion)
- Bound every A4 question to an explicit time window — source: RESULTS-v0.2.md (limitation 1)
- Restructure A3 into core vs sanity control (A3n), add hard negatives
  (published-but-not-yet-in-force; staged commencement as a hard class) — source:
  RESULTS-v0.2.md (findings item 4, Human legal review, limitation 2)
- Remove the leftover no-signal item A3y-DU-2023-1450 — source:
  analysis/analyzer-abstention-incident.md; RESULTS-v0.2.md (limitation 4)
- Prompt-level response protocol, defined and parsed once for every model, with a
  rerun — source: RESULTS-v0.2.md (limitation 6); analysis/format-compliance-v0.2.md
  (What this does not do)

## Later
- Paper, including a hierarchical (act-level, draw-aware) bootstrap in place of
  min–max draw ranges — source: README.md (Citation: "Paper: in preparation");
  RESULTS-v0.2.md (limitation 7)

## Done
- Flat response file counts as one draw, as a whole-model alternative — PR #5
  (5cb676e, 9009974, bf78285), 2026-09-02
- Format compliance reported apart from semantic correctness: `scripts/score_protocol.py`
  (`--self-check` against published figures), `analysis/format-compliance-v0.2.md`,
  `tests/test_score_protocol.py`, Tests CI `.github/workflows/tests.yml` — PR #4 (e930307), 2026-09-02
- Analyzer-abstention hardening recorded in RESULTS-v0.2 — PR #3 (47e04fb), 2026-08-26
- CI verifies published checksums on every change: `.github/workflows/checksums.yml` —
  PR #2 (915cbf9), 2026-08-19
- Symmetric full-coverage rule in the analyzer — PR #1 (aa23357), 2026-08-18
- v0.2 freeze (pre-PR history, 2026-08-14/15):
  - final N values, diagnostic-challenge-set framing, dataset checksums
    `CHECKSUMS-v0.2.txt` — b3b9078
  - three-metric reporting, analyzer incident forensics, strictness audit, full repro
    pack (`analysis/`, `models-v0.2.json`, `valid-draws-v0.2.json`, `scripts/build_track_a.py`) — e48da90
  - post-quarantine instability numbers, canary asymmetry note — 2aa2502
  - golds verified, one item quarantined, 79 scored (`REVIEW-v0.2.md`, `quarantine.json`) — 98c4f72
  - CC BY 4.0 legal code, liability disclaimer, retrieval dates (`LICENSE`, README) — dfe92e7
  - repository URL in citation metadata (`CITATION.cff`) — 1f4405c
  - public benchmark skeleton: `questions.json`, `nuggets.json`, `scripts/run_models.py`,
    `scripts/score_nuggets.py`, `scripts/analyze_failures.py` — 0088e13

## Unverified
- Pruning the 14 no-signal items "in v0.3" — REVIEW-v0.2.md (Cut candidates) names a
  v0.3, but every later document routes changes to v1.0; whether a v0.3 is still
  planned is not recorded.
- Paper status — README says "in preparation"; no public draft or branch, so it is not
  listed under Now.

## Sources
- README.md, RESULTS-v0.2.md, REVIEW-v0.2.md, CITATION.cff, LICENSE
- analysis/analyzer-abstention-incident.md, analysis/strictness-audit-v0.2.md,
  analysis/format-compliance-v0.2.md
- .github/workflows/tests.yml, .github/workflows/checksums.yml
- `git log` of `main` (19 commits, 0088e13 … 65f1c43)
- `gh pr list -R bartoszkobylinski/pl-temporal --state all` (5 PRs, all merged)
- `gh issue list -R bartoszkobylinski/pl-temporal --state all` (0 issues)
- grep for TODO/FIXME/planned/v0.3/v1.0 across tracked .md/.py files (no TODO/FIXME found;
  no CLAUDE.md/AGENTS.md tracked)
