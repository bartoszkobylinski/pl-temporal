# Strictness audit — could substring nuggets credit ambiguous answers? (2026-08-15)

Concern (external review): the date matcher checks whether the gold date appears
ANYWHERE in the answer, and the binary matcher searches for TAK/NIE anywhere — an
answer like "I considered 2004-04-20, but the correct date is 2004-05-01" could be
credited on the wrong grounds, and an answer containing both TAK and NIE could pass.

Method: `analysis/strictness_audit.py` over every answered (non-bucketed) response
in the valid v0.2 draws — 2,303 responses, 31 run files, 79 questions. Raw counts in
`strictness-audit-v0.2.txt`.

| class | count | verdict |
|---|---:|---|
| A1 answers with >1 distinct ISO date | **0** / 2,303 | the hypothesized class never occurred |
| A1 answers with gold date + another date | **0** | — |
| A2 answers with >1 Dz.U. position mention | 24 | all are verbose claude-opus-5 answers; follow-up check: **0** of them were scored correct with a non-gold position listed first — no false credit |
| A3/A4 answers containing both TAK and NIE | 1 | gold-TAK item answered "**TAK** …" with the ordinary Polish word "nie" later in the prose; the gold-TAK nugget does not test NIE — no false credit |
| answers longer than 120 chars (reasoning around the answer) | 335 | verbosity, not ambiguity; covered by the classes above |

## Conclusion

Audited format analysis found **no ambiguous multi-answer outputs affecting scoring**
in the evaluated runs. The current substring matcher is empirically sufficient for
v0.2. Deterministic answer extraction + canonical comparison remains planned for
v1.0 as defense-in-depth (the audit protects this run, not future model behaviors).
