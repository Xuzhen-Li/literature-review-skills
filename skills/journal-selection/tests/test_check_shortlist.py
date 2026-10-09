"""Tests for the journal shortlist checker."""

import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from check_shortlist import HEADERS, check_shortlist  # noqa: E402

TODAY = date(2026, 10, 9)
TEMPLATE = Path(__file__).resolve().parents[1] / "references" / "shortlist_template.md"


def _row(name, url, accepts="yes", invited="no"):
    return {
        "journal": name,
        "publisher": f"Publisher {name}",
        "article_type": "Review",
        "accepts_reviews": accepts,
        "invited_only": invited,
        "oa_model": "hybrid",
        "apc": "[VERIFY]",
        "word_limit": "8000",
        "indexing": "[VERIFY]",
        "turnaround": "not stated",
        "fit": "Scope matches the locked outline.",
        "verified": f"verified on 2026-10-09 at {url}",
    }


def _doc(rows, extra=""):
    header = "| " + " | ".join(HEADERS) + " |"
    separator = "| " + " | ".join("---" for _ in HEADERS) + " |"
    body = ["| " + " | ".join(row[column] for column in HEADERS) + " |" for row in rows]
    tail = """
Recommended: Journal A
Backup: Journal B
Double-anonymized: no
Reference style: Vancouver
"""
    return "\n".join([header, separator, *body, tail, extra])


def test_template_header_and_valid_shortlist():
    header = next(line for line in TEMPLATE.read_text(encoding="utf-8").splitlines() if line.startswith("| journal"))
    cells = [cell.strip() for cell in header.strip().strip("|").split("|")]
    assert cells == list(HEADERS)
    rows = [
        _row("Journal A", "https://journal-a.test/for-authors"),
        _row("Journal B", "https://journal-b.test/for-authors"),
        _row("Journal C", "https://journal-c.test/for-authors"),
    ]
    assert check_shortlist(_doc(rows), TODAY) == []


def test_blocks_bad_urls_dates_and_invited_only():
    rows = [
        _row("Journal A", "https://journal.example/authors"),
        _row("Journal B", "https://journal-b.test/for-authors"),
        _row("Journal C", "https://en.wikipedia.org/wiki/Journal"),
    ]
    errors = check_shortlist(_doc(rows), TODAY)
    assert any("example" in error for error in errors)
    assert any("wikipedia.org" in error for error in errors)
    future = _row("Journal A", "https://journal-a.test/for-authors")
    future["verified"] = "verified on 2026-10-10 at https://journal-a.test/for-authors"
    dated = check_shortlist(
        _doc([future, _row("Journal B", "https://journal-b.test/for-authors"), _row("Journal C", "https://journal-c.test/for-authors")]),
        TODAY,
    )
    assert any("future" in error for error in dated)
    invited = [
        _row("Journal A", "https://journal-a.test/for-authors", invited="yes"),
        _row("Journal B", "https://journal-b.test/for-authors"),
        _row("Journal C", "https://journal-c.test/for-authors"),
    ]
    assert any("invitation" in error for error in check_shortlist(_doc(invited), TODAY))
    invited_ok = _doc(invited, extra="Invitation for Journal A: yes\n")
    assert check_shortlist(invited_ok, TODAY) == []


def test_partition_and_metric_need_an_official_page_from_that_day():
    rows = [
        _row("Journal A", "https://journal-a.test/for-authors"),
        _row("Journal B", "https://journal-b.test/for-authors"),
        _row("Journal C", "https://journal-c.test/for-authors"),
    ]
    bare = _doc(rows, extra="National partition for Journal A: Q1\n")
    assert any("Partition source" in error for error in check_shortlist(bare, TODAY))
    sourced = _doc(
        rows,
        extra=(
            "National partition for Journal A: Q1\n"
            "Partition source for Journal A: verified on 2026-10-09 at https://jcr.clarivate.com/journal-a\n"
            "Citation metric for Journal A: 4.2 (2024 Journal Impact Factor)\n"
            "Metric source for Journal A: verified on 2026-10-09 at https://jcr.clarivate.com/journal-a\n"
        ),
    )
    assert check_shortlist(sourced, TODAY) == []
    jcr_quartile = _doc(
        rows,
        extra=(
            "Citation metric for Journal A: Q1 (2024 JCR quartile)\n"
            "Metric source for Journal A: verified on 2026-10-09 at https://jcr.clarivate.com/journal-a\n"
        ),
    )
    assert check_shortlist(jcr_quartile, TODAY) == []
    matcher = sourced.replace("https://jcr.clarivate.com/journal-a", "https://www.scimagojr.com/journalsearch.php", 1)
    assert any("not an official page" in error for error in check_shortlist(matcher, TODAY))
    remembered = _doc(rows, extra="Impact factor: 4.2\n")
    assert any("citation metric" in error for error in check_shortlist(remembered, TODAY))
