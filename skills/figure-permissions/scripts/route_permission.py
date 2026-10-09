#!/usr/bin/env python3
"""Route a figure to attribute, request, redraw, or stop."""

from __future__ import annotations

import argparse
import csv
import io
import json
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional, Sequence
from urllib.parse import urlparse

TYPES = {"original", "adapted", "reused"}
LICENSES = {
    "original",
    "cc-by",
    "cc-by-sa",
    "cc-by-nc",
    "cc-by-nc-sa",
    "cc-by-nd",
    "cc-by-nc-nd",
    "cc0",
    "public-domain",
    "publisher-owned",
    "own-previous",
    "unknown",
}
ACTIONS = {
    "not_required",
    "fix_type",
    "attribute",
    "attribute_check_sharealike",
    "credit_recommended",
    "request_or_replace",
    "reuse_unmodified_only",
    "do_not_adapt",
    "request_rightslink",
    "check_agreement",
    "stop_and_verify",
}
LOG_COLUMNS = (
    "figure_id",
    "source_citation",
    "source_url",
    "license",
    "route_action",
    "request_needed",
    "request_date",
    "grant_date",
    "grant_reference",
    "credit_line",
    "blocker",
)
ID_RE = re.compile(r"^(?:Fig\. \d+[a-z]?|Table \d+[a-z]?|Box \d+[a-z]?)$")
BLOCKED_HOST_PARTS = ("sci-hub", "libgen", "researchgate.net", "academia.edu")


def route(item_type: str, license_name: str) -> Dict[str, object]:
    """Return the permissions action for one ledger row.

    request_needed means a person must confirm journal policy or obtain a
    grant before the figure is used. It does not mean this program sends mail.
    """
    item_type = item_type.strip().lower()
    license_name = license_name.strip().lower()
    if item_type not in TYPES:
        raise ValueError(f"unknown type: {item_type}")
    if license_name not in LICENSES:
        raise ValueError(f"unknown license: {license_name}")

    if item_type == "original":
        if license_name != "original":
            return _result(
                "fix_type",
                True,
                False,
                "An original figure uses license original. Reclassify the row.",
            )
        return _result(
            "not_required",
            False,
            True,
            "Original expression created for this manuscript.",
        )
    if license_name == "original":
        return _result(
            "fix_type",
            True,
            False,
            "A copied or redrawn source cannot use license original.",
        )
    if license_name == "unknown":
        return _result(
            "stop_and_verify",
            True,
            False,
            "Read the license on the version-of-record page before any reuse.",
        )
    if license_name == "own-previous":
        return _result(
            "check_agreement",
            True,
            False,
            "Read the version-of-record license or the publishing agreement, then route again.",
        )
    if license_name == "cc-by":
        return _result(
            "attribute",
            False,
            True,
            "CC BY allows reuse and adaptation with attribution.",
        )
    if license_name == "cc-by-sa":
        return _result(
            "attribute_check_sharealike",
            True,
            True,
            "ShareAlike may conflict with a journal copyright transfer. Confirm before use.",
        )
    if license_name in {"cc-by-nc", "cc-by-nc-sa"}:
        return _result(
            "request_or_replace",
            True,
            True,
            "CC BY-NC and CC BY-NC-SA allow adaptation. Do not treat journal publication as non-commercial. Request permission or replace the figure.",
        )
    if license_name == "cc-by-nd":
        if item_type == "adapted":
            return _result(
                "do_not_adapt",
                True,
                False,
                "NoDerivatives does not allow this adaptation. Redraw without copying the expression, or request a separate license.",
            )
        return _result(
            "reuse_unmodified_only",
            False,
            False,
            "Unmodified reuse only, with attribution. No crop, recolor, or relabel.",
        )
    if license_name == "cc-by-nc-nd":
        if item_type == "adapted":
            return _result(
                "do_not_adapt",
                True,
                False,
                "NoDerivatives does not allow this adaptation.",
            )
        return _result(
            "request_or_replace",
            True,
            False,
            "NonCommercial plus NoDerivatives. Request permission or replace the figure.",
        )
    if license_name in {"cc0", "public-domain"}:
        return _result(
            "credit_recommended",
            False,
            True,
            "No permission request. Add a scholarly credit line anyway.",
        )
    return _result(
        "request_rightslink",
        True,
        False,
        "Publisher-owned. The user starts from the article's permission button or the publisher desk.",
    )


def _result(
    action: str, request_needed: bool, adaptation_allowed: bool, notes: str
) -> Dict[str, object]:
    if action not in ACTIONS:
        raise ValueError(action)
    return {
        "action": action,
        "request_needed": request_needed,
        "adaptation_allowed": adaptation_allowed,
        "notes": notes,
    }


def _blocked(url: str) -> bool:
    host = (urlparse(url).hostname or "").lower()
    return (not host) or any(part in host for part in BLOCKED_HOST_PARTS)


def validate_log(text: str) -> List[str]:
    """Validate 12-permissions/permissions_log.csv. An empty error list means pass."""
    reader = csv.DictReader(io.StringIO(text))
    if reader.fieldnames:
        reader.fieldnames = [name.strip() for name in reader.fieldnames]
    missing = [column for column in LOG_COLUMNS if column not in (reader.fieldnames or [])]
    if missing:
        return [f"permissions log missing columns: {', '.join(missing)}"]
    errors: List[str] = []
    rows = list(reader)
    if not rows:
        return ["permissions log has no rows"]
    for index, raw in enumerate(rows, start=2):
        row = {key: (raw.get(key) or "").strip() for key in LOG_COLUMNS}
        prefix = f"row {index} ({row['figure_id'] or 'blank'})"
        if not ID_RE.match(row["figure_id"]):
            errors.append(f"{prefix} bad figure_id")
        if row["route_action"] == "not_required":
            errors.append(f"{prefix} originals do not belong in the permissions log")
        elif row["route_action"] not in ACTIONS:
            errors.append(f"{prefix} unknown route_action")
        if row["request_needed"] not in {"yes", "no"}:
            errors.append(f"{prefix} request_needed must be yes or no")
        if row["source_url"] and (
            not row["source_url"].startswith("https://") or _blocked(row["source_url"])
        ):
            errors.append(f"{prefix} source_url is not allowed")
        if row["route_action"] == "do_not_adapt":
            if row["blocker"] == "":
                errors.append(f"{prefix} do_not_adapt needs a blocker")
            if row["credit_line"] != "REMOVED" and not row["credit_line"].startswith(
                "Replaced by "
            ):
                errors.append(
                    f"{prefix} do_not_adapt credit_line must be REMOVED or 'Replaced by ...'"
                )
        if (
            row["request_needed"] == "yes"
            and row["grant_date"] == ""
            and row["blocker"] == ""
            and row["route_action"] != "do_not_adapt"
        ):
            errors.append(f"{prefix} open request needs a blocker note")
        if row["grant_date"] and row["grant_reference"] == "":
            errors.append(f"{prefix} a grant date needs a grant reference")
    return errors


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("item_type", nargs="?")
    parser.add_argument("license_name", nargs="?")
    parser.add_argument("--log", type=Path)
    args = parser.parse_args(argv)
    exit_code = 0
    if args.item_type or args.license_name:
        if not args.item_type or not args.license_name:
            print("ERROR need both a type and a license", file=sys.stderr)
            return 2
        try:
            print(json.dumps(route(args.item_type, args.license_name), indent=2))
        except ValueError as exc:
            print(f"ERROR {exc}", file=sys.stderr)
            return 2
    if args.log:
        errors = validate_log(args.log.read_text(encoding="utf-8"))
        if errors:
            for error in errors:
                print(f"ERROR {error}", file=sys.stderr)
            exit_code = 1
        elif not (args.item_type or args.license_name):
            print("OK permissions log")
    if not args.log and not (args.item_type or args.license_name):
        parser.error("provide a type and license, or --log")
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
