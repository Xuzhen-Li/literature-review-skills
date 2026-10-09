"""Tests for the reviewer-response checker."""

import csv
import io
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from check_response import check_response, main  # noqa: E402

QUOTE = "Evidence from two field trials indicates a yield gain."
REVISED = (
    "We have revised the sentence on p. 3, lines 40-44 so the wording matches the two trials. "
    + QUOTE
)
DECLINED = (
    "We have not changed this paragraph. The requested analysis is outside the stated scope of the review."
)
CLARIFIED = "The search date is already stated in the Methods, and that sentence can stand."


def _manuscript():
    lines = [f"filler {number}" for number in range(1, 40)]
    lines.append(QUOTE)
    return "\n".join(lines) + "\n"


def _bundle(rows):
    buffer = io.StringIO()
    writer = csv.DictWriter(
        buffer,
        fieldnames=["comment_id", "action", "location", "change_quote", "response"],
    )
    writer.writeheader()
    writer.writerows(rows)
    letter = ["# Response to reviewers", ""]
    plan = ["# Action plan", ""]
    for row in rows:
        letter.extend([f"## {row['comment_id']}", "", row["response"], ""])
        plan.extend([f"## {row['comment_id']}", f"- Action: {row['action']}", ""])
    files = {"10-polish/manuscript.md": _manuscript()}
    return buffer.getvalue(), "\n".join(letter), "\n".join(plan), files


def _rows():
    return [
        {
            "comment_id": "E.1",
            "action": "clarified",
            "location": "none",
            "change_quote": "none",
            "response": CLARIFIED,
        },
        {
            "comment_id": "R1.1",
            "action": "revised",
            "location": "10-polish/manuscript.md lines 40-40",
            "change_quote": QUOTE,
            "response": REVISED,
        },
        {
            "comment_id": "R1.2",
            "action": "declined",
            "location": "none",
            "change_quote": "none",
            "response": DECLINED,
        },
    ]


def test_complete_response_passes():
    table, letter, plan, files = _bundle(_rows())
    assert check_response(table, letter, files, plan) == []


def test_revision_must_match_the_file_and_cite_lines():
    rows = _rows()
    rows[1]["location"] = "10-polish/manuscript.md lines 1-2"
    table, letter, plan, files = _bundle(rows)
    assert any("not in the cited lines" in error for error in check_response(table, letter, files, plan))
    rows = _rows()
    rows[1]["response"] = "We have revised the sentence without a page reference. " + QUOTE
    table, letter, plan, files = _bundle(rows)
    assert any("p. N" in error for error in check_response(table, letter, files, plan))
    rows = _rows()
    rows[2]["response"] = "We have revised this after all, on p. 3, lines 40-44, but the action stays declined."
    table, letter, plan, files = _bundle(rows)
    assert any("must not say the text was revised" in error for error in check_response(table, letter, files, plan))


def test_numbering_and_cli(tmp_path):
    rows = _rows()
    rows[1]["comment_id"] = "R2.1"
    table, letter, plan, files = _bundle(rows)
    assert any("R1, R2" in error or "gaps" in error for error in check_response(table, letter, files, plan))
    rows = _rows()
    table, letter, plan, files = _bundle(rows)
    root = tmp_path / "project"
    (root / "10-polish").mkdir(parents=True)
    (root / "10-polish" / "manuscript.md").write_text(files["10-polish/manuscript.md"], encoding="utf-8")
    (root / "14-revision").mkdir()
    (root / "14-revision" / "response_table.csv").write_text(table, encoding="utf-8")
    (root / "14-revision" / "response.md").write_text(letter, encoding="utf-8")
    (root / "14-revision" / "action_plan.md").write_text(plan, encoding="utf-8")
    assert main([
        "--table", str(root / "14-revision" / "response_table.csv"),
        "--letter", str(root / "14-revision" / "response.md"),
        "--plan", str(root / "14-revision" / "action_plan.md"),
        "--root", str(root),
    ]) == 0
