"""Tests for citation keys and manuscript coverage."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from check_citations import check_finished_draft, check_manuscript, check_section, main  # noqa: E402

IDS = {"E014", "E015"}


def _section(prose, header_ids="E014, E015", budget_ok=True):
    body = prose
    if budget_ok:
        body = prose + " " + " ".join(f"word{i}" for i in range(80))
    return f"""# S2. Shared findings

- Outline claim: Two studies agree.
- Word budget: 100
- Evidence IDs: {header_ids}

## Prose

{body}
"""


def test_accepts_three_citation_shapes():
    prose = (
        "Both reports point the same way (Smith et al., 2020; E014; Lee and Kim, 2021; E015). "
        "One earlier note agrees (Smith, 2019; E014)."
    )
    assert check_section(_section(prose), IDS, budget=100) == []


def test_rejects_malformed_bare_ids_and_markers():
    bare = check_section(_section("The effect size was 2.4 in E014."), IDS, budget=100)
    assert any("outside a citation" in error for error in bare)
    bad = check_section(_section("A report agrees (Smith et al. 2020; E014)."), IDS, budget=100)
    assert any("malformed citation" in error for error in bad)
    marked = check_section(_section("The gap remains [NEEDS SOURCE] (Smith, 2020; E014)."), IDS, budget=100)
    assert any("NEEDS SOURCE" in error for error in marked)


def test_header_must_match_prose_and_budget():
    prose = "Only one source is cited (Smith, 2020; E014)."
    mismatch = check_section(_section(prose, "E014, E015"), IDS, budget=100)
    assert any("not cited" in error for error in mismatch)
    short = "Short note (Smith, 2020; E014)."
    counted = check_section(_section(short, "E014", budget_ok=False), IDS, budget=100)
    assert any("word count" in error for error in counted)


def test_manuscript_coverage_and_cli(tmp_path):
    outline = "- Evidence IDs: E014, E015\n"
    manuscript = "Agreement is limited (Smith et al., 2020; E014).\n<!-- E015 -->\n"
    log = "id,reason\nC001,dropped nothing but E015 stays\n"
    # E015 is in a comment, so it is cited. No drop required.
    assert check_manuscript(manuscript, outline, log, IDS) == []
    missing = check_manuscript(
        "Agreement is limited (Smith et al., 2020; E014).\n",
        outline,
        "reason,none\n",
        IDS,
    )
    assert any("dropped E015" in error or "E015" in error for error in missing)
    dropped = check_manuscript(
        "Agreement is limited (Smith et al., 2020; E014).\n",
        outline,
        "reason\ndropped E015 because it was out of scope\n",
        IDS,
    )
    assert dropped == []
    section = tmp_path / "S02.md"
    evidence = tmp_path / "evidence.csv"
    section.write_text(_section(
        "Both reports point the same way (Smith et al., 2020; E014; Lee, 2021; E015)."
    ), encoding="utf-8")
    evidence.write_text("evidence_id,note\nE014,a\nE015,b\n", encoding="utf-8")
    assert main([str(section), "--budget", "100", "--evidence", str(evidence)]) == 0


def test_finished_draft_requires_checked_limitations_and_next_questions(tmp_path):
    outline = """## S4. Limitations

## S5. Next questions

## S6. Conclusions
"""
    drafts = tmp_path / "drafts"
    drafts.mkdir()
    (drafts / "S04-limitations.md").write_text("- Status: draft\n", encoding="utf-8")
    (drafts / "S05-next-questions.md").write_text("- Status: checked\n", encoding="utf-8")
    (tmp_path / "outline.md").write_text(outline, encoding="utf-8")
    missing = check_finished_draft(outline, {5: "- Status: checked\n"})
    assert any("Limitations" in error for error in missing)
    unchecked = check_finished_draft(
        outline,
        {4: "- Status: draft\n", 5: "- Status: checked\n"},
    )
    assert any("not Status: checked" in error for error in unchecked)
    assert check_finished_draft(
        outline,
        {4: "- Status: checked\n", 5: "- Status: checked\n"},
    ) == []
    assert main(["--finish", "--outline", str(tmp_path / "outline.md"), "--drafts", str(drafts)]) == 1
    (drafts / "S04-limitations.md").write_text("- Status: checked\n", encoding="utf-8")
    assert main(["--finish", "--outline", str(tmp_path / "outline.md"), "--drafts", str(drafts)]) == 0
