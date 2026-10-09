"""Tests for the permissions router and log."""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from route_permission import ACTIONS, main, route, validate_log  # noqa: E402

TREE = Path(__file__).resolve().parents[1] / "references" / "decision_tree.md"

CASES = [
    ("original", "original", "not_required", False, True),
    ("original", "cc-by", "fix_type", True, False),
    ("adapted", "original", "fix_type", True, False),
    ("reused", "cc-by", "attribute", False, True),
    ("adapted", "cc-by", "attribute", False, True),
    ("adapted", "cc-by-sa", "attribute_check_sharealike", True, True),
    ("reused", "cc-by-nc", "request_or_replace", True, True),
    ("adapted", "cc-by-nc-sa", "request_or_replace", True, True),
    ("reused", "cc-by-nd", "reuse_unmodified_only", False, False),
    ("adapted", "cc-by-nd", "do_not_adapt", True, False),
    ("adapted", "cc-by-nc-nd", "do_not_adapt", True, False),
    ("reused", "cc-by-nc-nd", "request_or_replace", True, False),
    ("reused", "cc0", "credit_recommended", False, True),
    ("adapted", "public-domain", "credit_recommended", False, True),
    ("reused", "publisher-owned", "request_rightslink", True, False),
    ("adapted", "own-previous", "check_agreement", True, False),
    ("reused", "unknown", "stop_and_verify", True, False),
]


def test_routes_and_decision_tree_agree():
    fence = TREE.read_text(encoding="utf-8").split("```")[1]
    listed = {line.strip() for line in fence.splitlines() if line.strip()}
    assert listed == ACTIONS
    for item_type, license_name, action, request_needed, adaptation_allowed in CASES:
        result = route(item_type, license_name)
        assert result["action"] == action
        assert result["request_needed"] is request_needed
        assert result["adaptation_allowed"] is adaptation_allowed


def test_sharealike_note_and_unknown_license():
    assert "ShareAlike" in route("adapted", "cc-by-sa")["notes"]
    try:
        route("adapted", "made-up")
    except ValueError as exc:
        assert "unknown license" in str(exc)
    else:
        raise AssertionError("expected ValueError")


def test_log_and_cli(tmp_path):
    log = """figure_id,source_citation,source_url,license,route_action,request_needed,request_date,grant_date,grant_reference,credit_line,blocker
Fig. 2,Smith 2020,https://journal-a.test/article,cc-by-nd,do_not_adapt,yes,2026-10-09,,,REMOVED,ND license blocks adaptation
"""
    assert validate_log(log) == []
    bad = log.replace("REMOVED", "Adapted from Smith")
    assert any("REMOVED" in error for error in validate_log(bad))
    path = tmp_path / "log.csv"
    path.write_text(log, encoding="utf-8")
    assert main(["--log", str(path)]) == 0
    printed = main(["reused", "cc-by"])
    assert printed == 0
    payload = json.loads(
        __import__("subprocess").check_output(
            [sys.executable, str(Path(__file__).resolve().parents[1] / "scripts" / "route_permission.py"), "reused", "cc-by"],
            text=True,
        )
    )
    assert payload["action"] == "attribute"
