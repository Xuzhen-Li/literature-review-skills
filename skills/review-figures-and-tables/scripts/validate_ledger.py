#!/usr/bin/env python3
"""Validate 08-figures/figure_ledger.csv."""

from __future__ import annotations

import argparse
import csv
import io
import re
import sys
from pathlib import Path
from typing import List, Optional, Sequence, Set
from urllib.parse import urlparse

REQUIRED = (
    "id",
    "type",
    "sources",
    "license",
    "permission_status",
    "caption_credit",
)
TYPES = {"original", "adapted", "reused"}
STATUSES = {"not_required", "needed", "requested", "granted"}
RESOLVED = {
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
}
UNRESOLVED = {"unknown", "own-previous"}
NO_REQUEST = {"cc-by", "cc0", "public-domain"}
CC_URL_PREFIX = {
    "cc-by": "https://creativecommons.org/licenses/by/",
    "cc-by-sa": "https://creativecommons.org/licenses/by-sa/",
    "cc-by-nc": "https://creativecommons.org/licenses/by-nc/",
    "cc-by-nc-sa": "https://creativecommons.org/licenses/by-nc-sa/",
    "cc-by-nd": "https://creativecommons.org/licenses/by-nd/",
    "cc-by-nc-nd": "https://creativecommons.org/licenses/by-nc-nd/",
    "cc0": "https://creativecommons.org/publicdomain/zero/",
}
ID_COLUMNS = ("evidence_id", "id")
ID_RE = re.compile(r"^(?:Fig\. \d+[a-z]?|Table \d+[a-z]?|Box \d+[a-z]?)$")
EVIDENCE_RE = re.compile(r"\bE\d{3,}\b")
BLOCKED_HOST_PARTS = (
    "wikipedia.org",
    "researchgate.net",
    "academia.edu",
    "reddit.com",
    "medium.com",
    "twitter.com",
    "facebook.com",
    "linkedin.com",
    "youtube.com",
    "bilibili.com",
    "doi.org",
    "sci-hub",
    "libgen",
)


def load_evidence_ids(path: Path) -> Set[str]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames:
            raise ValueError(f"{path} has no header")
        fields = [name.strip() for name in reader.fieldnames]
        reader.fieldnames = fields
        column = next((name for name in ID_COLUMNS if name in fields), None)
        if column is None:
            raise ValueError(f"{path} needs a column named evidence_id or id")
        return {
            (row.get(column) or "").strip()
            for row in reader
            if (row.get(column) or "").strip()
        }


def _blocked(url: str) -> bool:
    host = (urlparse(url).hostname or "").lower()
    if not host or "." not in host:
        return True
    if host == "example.com" or host.endswith(".example") or host.endswith(".example.com"):
        return True
    return any(part in host for part in BLOCKED_HOST_PARTS)


def _credit_ok(item_type: str, credit: str) -> bool:
    if item_type == "original":
        return credit.startswith("Created for this review.")
    if item_type == "reused":
        return credit.startswith("Reproduced from ")
    if item_type == "adapted":
        return credit.startswith("Adapted from ")
    return False


def _read_rows(text: str):
    reader = csv.DictReader(io.StringIO(text))
    if reader.fieldnames:
        reader.fieldnames = [name.strip() for name in reader.fieldnames]
    rows = []
    for row in reader:
        rows.append(
            {
                key: (value or "").strip()
                for key, value in row.items()
                if isinstance(key, str) and isinstance(value, str)
            }
        )
    return reader.fieldnames or [], rows


def validate_ledger(
    text: str,
    evidence_ids: Optional[Set[str]] = None,
    strict: bool = False,
) -> List[str]:
    """Validate ledger CSV text. strict=True is the pre-submission check."""
    errors: List[str] = []
    fieldnames, rows = _read_rows(text)
    missing = [column for column in REQUIRED if column not in fieldnames]
    if missing:
        return [f"missing columns: {', '.join(missing)}"]
    if not rows:
        return ["ledger has no rows"]

    seen = set()
    for index, row in enumerate(rows, start=2):
        ident = row["id"]
        item_type = row["type"].lower()
        sources = row["sources"]
        license_name = row["license"].lower()
        status = row["permission_status"].lower()
        credit = row["caption_credit"]
        prefix = f"row {index} ({ident or 'blank'})"
        if not ID_RE.match(ident):
            errors.append(f"{prefix} id must look like 'Fig. 1', 'Table 1', or 'Box 1'")
        if ident in seen:
            errors.append(f"{prefix} duplicate id")
        seen.add(ident)
        if item_type not in TYPES:
            errors.append(f"{prefix} type must be original, adapted, or reused")
            continue
        if status not in STATUSES:
            errors.append(f"{prefix} bad permission_status")
            continue
        if re.search(r"sci-hub|libgen", sources, re.I):
            errors.append(f"{prefix} sources name a shadow library")
        license_url = row.get("license_url", "")
        if license_url:
            if not license_url.startswith("https://") or _blocked(license_url):
                errors.append(f"{prefix} license_url is not an allowed https URL")
            prefix_needed = CC_URL_PREFIX.get(license_name)
            if prefix_needed and not license_url.startswith(prefix_needed):
                errors.append(f"{prefix} license_url does not match {license_name}")

        if item_type == "original":
            if status != "not_required":
                errors.append(f"{prefix} original items use permission_status not_required")
            if sources.lower() != "none":
                errors.append(f"{prefix} original items must set sources to none")
            if license_name != "original":
                errors.append(f"{prefix} original items use license original")
            if not _credit_ok("original", credit):
                errors.append(
                    f"{prefix} caption_credit must start with 'Created for this review.'"
                )
            continue

        found_ids = EVIDENCE_RE.findall(sources)
        if sources.lower() in {"", "none"} or not found_ids:
            errors.append(f"{prefix} {item_type} items need an evidence ID in sources")
        elif evidence_ids is not None:
            unknown = [item for item in found_ids if item not in evidence_ids]
            if unknown:
                errors.append(f"{prefix} unknown evidence IDs: {', '.join(unknown)}")

        if license_name not in RESOLVED and license_name not in UNRESOLVED:
            errors.append(f"{prefix} unknown license value")
            continue

        if license_name in UNRESOLVED:
            if status != "needed" or credit != "PENDING":
                errors.append(
                    f"{prefix} unresolved license must stay needed with PENDING credit"
                )
            if strict:
                errors.append(f"{prefix} license {license_name} is not cleared")
            continue

        no_request = license_name in NO_REQUEST or (
            license_name == "cc-by-nd" and item_type == "reused"
        )
        if license_name == "cc-by-nd" and item_type == "adapted":
            no_request = False
        if not no_request and status == "not_required":
            errors.append(f"{prefix} this license cannot use permission_status not_required")
        if status in {"not_required", "granted"} and not _credit_ok(item_type, credit):
            errors.append(f"{prefix} final caption_credit has the wrong prefix")
        if status in {"needed", "requested"} and credit != "PENDING" and not _credit_ok(
            item_type, credit
        ):
            errors.append(f"{prefix} use PENDING or a final credit line")
        if strict and status not in {"not_required", "granted"}:
            errors.append(f"{prefix} status {status} is not cleared for submission")
        if strict and credit == "PENDING":
            errors.append(f"{prefix} caption_credit is still PENDING")

    fig1 = [row for row in rows if row["id"] == "Fig. 1"]
    if not fig1:
        errors.append("ledger is missing Fig. 1")
    elif fig1[0]["type"].lower() != "original":
        errors.append("Fig. 1 must be type original")
    return errors


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("ledger", type=Path)
    parser.add_argument("--evidence", required=True, type=Path)
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args(argv)
    try:
        evidence_ids = load_evidence_ids(args.evidence)
    except (OSError, ValueError) as exc:
        print(f"ERROR {exc}", file=sys.stderr)
        return 1
    text = args.ledger.read_text(encoding="utf-8")
    errors = validate_ledger(text, evidence_ids, strict=args.strict)
    if errors:
        for error in errors:
            print(f"ERROR {error}", file=sys.stderr)
        return 1
    print("OK ledger")
    return 0


if __name__ == "__main__":
    sys.exit(main())
