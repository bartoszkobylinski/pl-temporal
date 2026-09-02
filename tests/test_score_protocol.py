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
import json
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


def test_legacy_flat_response_is_selected_only_once(tmp_path, monkeypatch) -> None:
    """A model listed with several draws but only a flat responses/<name>.json has ONE
    draw on disk, not several copies of one. Found by the CI test author on the notebook
    mirror of this file. The committed corpus never triggers it - every response file is
    .drawN.json, so the flat fallback is dead code for this dataset and no published figure
    moves - but a v1.0 run made with --draws 1 would land straight in it."""
    (tmp_path / "valid-draws-v0.2.json").write_text(
        json.dumps({"valid_draws": {"model": [1, 2, 3]}}), encoding="utf-8")
    responses = tmp_path / "responses"
    responses.mkdir()
    (responses / "model.json").write_text("{}", encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    assert sp.valid_draw_paths("model") == ["responses/model.json"]


def test_per_draw_files_are_preferred_and_all_selected(tmp_path, monkeypatch) -> None:
    (tmp_path / "valid-draws-v0.2.json").write_text(
        json.dumps({"valid_draws": {"model": [1, 2]}}), encoding="utf-8")
    responses = tmp_path / "responses"
    responses.mkdir()
    for name in ("model.draw1.json", "model.draw2.json", "model.json"):
        (responses / name).write_text("{}", encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    assert sp.valid_draw_paths("model") == [
        "responses/model.draw1.json", "responses/model.draw2.json"]


def test_legacy_flat_response_does_not_fill_a_missing_numbered_draw(tmp_path, monkeypatch) -> None:
    """responses/<model>.json and <model>.draw1.json are the same single run under two
    names. With draw1 present, the flat file must not become a second observation because
    the manifest happens to list a draw that was never written."""
    (tmp_path / "valid-draws-v0.2.json").write_text(
        json.dumps({"valid_draws": {"model": [1, 2]}}), encoding="utf-8")
    responses = tmp_path / "responses"
    responses.mkdir()
    for name in ("model.draw1.json", "model.json"):
        (responses / name).write_text("{}", encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    assert sp.valid_draw_paths("model") == ["responses/model.draw1.json"]


def test_a_model_with_no_valid_draws_selects_nothing(tmp_path, monkeypatch) -> None:
    """gemini-3-flash is listed with an empty draw list; a flat file on disk must not
    resurrect it into the roster."""
    (tmp_path / "valid-draws-v0.2.json").write_text(
        json.dumps({"valid_draws": {"model": []}}), encoding="utf-8")
    responses = tmp_path / "responses"
    responses.mkdir()
    (responses / "model.json").write_text("{}", encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    assert sp.valid_draw_paths("model") == []
