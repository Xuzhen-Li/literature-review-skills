"""Tests for overclaim scanning, the change log, and assembly."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from assemble_manuscript import assemble  # noqa: E402
from polish_checks import (  # noqa: E402
    check_decisions,
    find_overclaims,
    load_phrases,
    validate_change_log,
)

PHRASES = Path(__file__).resolve().parents[1] / "references" / "overclaim_words.md"


def test_phrase_file_and_boundaries():
    loaded = load_phrases(PHRASES.read_text(encoding="utf-8"))
    block = {phrase for phrase, level in loaded if level == "block"}
    review = {phrase for phrase, level in loaded if level == "review"}
    assert {"proves", "for the first time", "we are the first", "clearly demonstrates"} <= block
    assert "significant" in review
    hits = find_overclaims("The assay disproves the claim.", loaded)
    assert hits == []
    hits = find_overclaims("This clearly demonstrates a gain for the first time.", loaded)
    assert [hit["phrase"] for hit in hits] == ["clearly demonstrates", "for the first time"]


def test_change_log_rejects_new_overclaim_and_accepts_a_hedge():
    phrases = [phrase for phrase, level in load_phrases(PHRASES.read_text(encoding="utf-8")) if level == "block"]
    bad = """id,file,location,change_type,before,after,reason
C001,10-polish/manuscript.md,lines 12-14,hedge,The data proved it,The data proves it,Still too strong for one study
"""
    assert any("proves" in error for error in validate_change_log(bad, phrases))
    good = """id,file,location,change_type,before,after,reason
C001,10-polish/manuscript.md,lines 12-14,hedge,The data proves it,The data is consistent with it,E014 is a single cohort
"""
    assert validate_change_log(good, phrases) == []
    deleted = """id,file,location,change_type,before,after,reason
C002,10-polish/manuscript.md,lines 20-22,cut_to_limit,A long aside stays, [deleted],Cut to the journal word limit
"""
    assert validate_change_log(deleted, phrases) == []


def test_review_decisions_and_assembly():
    phrases = load_phrases(PHRASES.read_text(encoding="utf-8"))
    hits = find_overclaims("The result was significant in one cohort.", phrases)
    missing = check_decisions(hits, "line\tphrase\tdecision\treason\n")
    assert any("no decision" in error for error in missing)
    kept = "line\tphrase\tdecision\treason\n1\tsignificant\tkept\tkept: E014 reports a statistical test\n"
    assert check_decisions(hits, kept) == []
    outline = "## S1. Introduction\n\n## S2. Conclusions\n"
    drafts = {
        1: "## Prose\n\nIntro paragraph (Smith, 2020; E001).\n",
        2: "## Prose\n\nClosing paragraph (Lee, 2021; E002).\n",
    }
    text = assemble(outline, drafts)
    assert text.index("Intro paragraph") < text.index("Closing paragraph")
    assert text.startswith("## Introduction\n")
