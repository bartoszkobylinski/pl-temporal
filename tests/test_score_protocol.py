"""Tests for the four-metric scorer.

Two things are pinned here, and they are not the same kind of thing.

1. An INVARIANT: abstention is classified before the answer parser runs. Violating it turns
   a decline into a correct answer on every item whose gold is `NIE`, because the abstention
   phrase "NIE WIEM" contains it. That is not hypothetical - `analyze_failures.py` shipped
   with exactly this bug (RESULTS-v0.2.md:111-119).

2. A REPRODUCTION: the recomputed semantic accuracy still equals what RESULTS-v0.2.md
   published. The frozen figures are what the repository is cited for; a scorer that quietly
   stops reproducing them is a worse failure than one that crashes.
"""
import importlib.util
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT / "scripts"))


def load(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


sp = load("score_protocol")

NIE_NUGGET = [{"kind": "regex", "pattern": r"\bNIE\b", "required": True}]
DATE_NUGGET = [{"kind": "exact", "value": "2007-04-04", "required": True}]
A3 = {"regime": "A3"}
A1 = {"regime": "A1"}


def test_abstention_is_classified_before_the_answer_parser() -> None:
    """"NIE WIEM" satisfies a gold of `\\bNIE\\b`. Order is the only thing preventing it."""
    outcome, conforming, semantic = sp.classify("NIE WIEM", A3, NIE_NUGGET)
    assert outcome == "abstained"
    assert not semantic
    assert not conforming
    # and the protocol verdict must not resurrect it through the other path
    assert not sp.protocol_ok("NIE WIEM", A3, NIE_NUGGET)


def test_a_real_negative_answer_is_still_correct_and_conforming() -> None:
    outcome, conforming, semantic = sp.classify("NIE", A3, NIE_NUGGET)
    assert (outcome, conforming, semantic) == ("correct", True, True)
    assert sp.protocol_ok("NIE", A3, NIE_NUGGET)


def test_transport_failures_are_not_answers() -> None:
    for payload in ("__ERROR__ HTTP 429", "__TRUNCATED__ stop_reason=max_tokens", ""):
        outcome, _, semantic = sp.classify(payload, A1, DATE_NUGGET)
        assert outcome in ("error", "truncated", "empty")
        assert not semantic


@pytest.mark.parametrize(
    "answer,bare,leading",
    [
        ("2007-04-04", True, True),
        ("**2007-04-04**", True, True),            # markdown is decoration, not a form change
        ("2007-04-04.", True, True),
        ("**2007-04-04** Ustawa weszła w życie 4 kwietnia.", False, True),
        ("Ustawa weszła w życie dnia 4 kwietnia 2007 r., czyli 2007-04-04.", False, False),
        ("4 kwietnia 2007 r.", False, False),      # right day, form the prompt did not ask for
    ],
)
def test_bare_and_leading_formats_are_distinguished(answer, bare, leading) -> None:
    assert (sp.parse_strict(answer, "A1") is not None) is bare
    assert (sp.parse_leading(answer, "A1") is not None) is leading


def test_semantic_credit_survives_a_non_conforming_answer() -> None:
    """The v0.2 rule is preserved exactly: nuggets match anywhere. Only the new columns
    know the answer ignored the requested form."""
    prose = "Ustawa weszła w życie dnia 4 kwietnia 2007 r., czyli 2007-04-04."
    outcome, conforming, semantic = sp.classify(prose, A1, DATE_NUGGET)
    assert (outcome, semantic) == ("correct", True)
    assert not conforming
    assert not sp.protocol_ok(prose, A1, DATE_NUGGET)


def test_protocol_credit_requires_the_answer_inside_the_conforming_span() -> None:
    """A bare answer of the right shape and the wrong value earns nothing."""
    assert sp.parse_strict("2007-04-05", "A1") is not None
    assert not sp.protocol_ok("2007-04-05", A1, DATE_NUGGET)


def test_leading_rule_does_not_match_a_longer_token() -> None:
    assert sp.parse_leading("2007-04-041 i coś dalej", "A1") is None


def test_published_v02_figures_are_still_reproduced() -> None:
    """End-to-end over the committed responses: ~0.1s, and it is the only guard that the
    frozen numbers and this scorer have not drifted apart."""
    proc = subprocess.run(
        [sys.executable, "scripts/score_protocol.py", "--self-check"],
        cwd=ROOT, capture_output=True, text=True,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "all published figures reproduced" in proc.stdout
