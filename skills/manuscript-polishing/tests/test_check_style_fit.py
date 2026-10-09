"""Tests for applying the post-lock style brief."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from check_style_fit import check_style_fit, main  # noqa: E402

BRIEF = """- Refreshed after journal lock: yes
- Locked journal: Journal A
- Heading pattern: Introduction | Limitations | Next questions | Conclusions
- Abstract shape: background; aim; scope; roadmap
- Figure budget: 2
"""

MANUSCRIPT = """## Abstract

**Background.** The field is broad. **Aim.** The question is narrow. **Scope.** Two settings are included. **Roadmap.** Later sections follow the evidence.

## Introduction

One claim (Smith, 2020; E001). See Fig. 1.

## Limitations

The samples are small (Lee, 2021; E002).

## Next questions

Whether a second setting agrees is still open (Lee, 2021; E002).

## Conclusions

The practical claim stays inside those settings (Smith, 2020; E001).
"""


def test_post_lock_brief_matches_headings_abstract_and_figure_budget():
    assert check_style_fit(BRIEF, MANUSCRIPT, "Journal A") == []
    stale = BRIEF.replace("yes", "no", 1)
    assert any("not been refreshed" in error for error in check_style_fit(stale, MANUSCRIPT, "Journal A"))
    extra = MANUSCRIPT.replace("See Fig. 1.", "See Fig. 1 and Fig. 2 and Fig. 3.")
    assert any("budget" in error for error in check_style_fit(BRIEF, extra, "Journal A"))
    swapped = MANUSCRIPT.replace("**Aim.**", "**Roadmap.**", 1)
    assert any("abstract is missing" in error for error in check_style_fit(BRIEF, swapped, "Journal A"))


def test_cli(tmp_path):
    brief = tmp_path / "style_brief.md"
    manuscript = tmp_path / "manuscript.md"
    brief.write_text(BRIEF, encoding="utf-8")
    manuscript.write_text(MANUSCRIPT, encoding="utf-8")
    assert main(["--brief", str(brief), "--manuscript", str(manuscript), "--journal", "Journal A"]) == 0
