"""Tests for the figure ledger."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from validate_ledger import main, validate_ledger  # noqa: E402

REF = Path(__file__).resolve().parents[1] / "references"
IDS = {"E010"}


def test_examples_pass():
    original = (REF / "figure_ledger_example.csv").read_text(encoding="utf-8")
    adapted = (REF / "figure_ledger_adapted_example.csv").read_text(encoding="utf-8")
    assert validate_ledger(original, IDS) == []
    assert validate_ledger(adapted, IDS, strict=True) == []


def test_fig1_must_be_original_and_sources_must_be_real():
    text = (REF / "figure_ledger_example.csv").read_text(encoding="utf-8")
    stolen = text.replace("Fig. 1,original,none,original", "Fig. 1,reused,E010,cc-by")
    assert any("Fig. 1 must be type original" in error for error in validate_ledger(stolen, IDS))
    assert any("unknown evidence" in error for error in validate_ledger(
        (REF / "figure_ledger_adapted_example.csv").read_text(encoding="utf-8"),
        {"E001"},
    ))


def test_publisher_owned_is_not_cleared_until_granted():
    text = """id,type,sources,license,permission_status,caption_credit
Fig. 1,original,none,original,not_required,Created for this review.
Fig. 2,reused,E010,publisher-owned,needed,PENDING
"""
    assert validate_ledger(text, IDS) == []
    assert any("not cleared" in error for error in validate_ledger(text, IDS, strict=True))


def test_shadow_library_and_cli(tmp_path):
    text = """id,type,sources,license,permission_status,caption_credit
Fig. 1,original,none,original,not_required,Created for this review.
Fig. 2,reused,E010 from sci-hub,cc-by,not_required,Reproduced from Smith et al., 2020.
"""
    assert any("shadow library" in error for error in validate_ledger(text, IDS))
    ledger = tmp_path / "figure_ledger.csv"
    evidence = tmp_path / "evidence.csv"
    ledger.write_text(
        (REF / "figure_ledger_example.csv").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    evidence.write_text("id,note\nE010,a\n", encoding="utf-8")
    assert main([str(ledger), "--evidence", str(evidence)]) == 0
