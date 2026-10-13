#!/usr/bin/env python3
"""Hand records to ASReview LAB and bring its labels back.

export: 02-records/library.csv -> a CSV that ASReview LAB imports
        (title, abstract, authors, doi, ...). Our record_id travels in
        the column lrs_record_id: ASReview keeps unknown input columns in
        its export but reserves record_id for its own index and strips
        input columns that start with asreview_. Optional prior labels
        from screening.csv go in the "included" column (1/0/empty).

import: an ASReview LAB CSV/TSV export -> rows in the screening.csv
        layout, written to a separate staging file. ASReview labels are
        relevance labels, not eligibility decisions: exclude rows get an
        empty reason_code and consensus stays empty, so a human still
        has to finish them. Records ASReview never showed ("not seen",
        empty asreview_label) are counted, never turned into excludes.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

ID_COLUMN = "lrs_record_id"
EXPORT_COLUMNS = [ID_COLUMN, "title", "abstract", "authors", "keywords", "doi", "year", "journal", "included"]
SCREENING_COLUMNS = ["record_id", "stage", "screener", "decision", "reason_code",
                     "reason_note", "date", "consensus"]
# Import never reads "included": it carries the prior labels we exported.
LABEL_COLUMNS = ["asreview_label", "label", "final_included", "label_included",
                 "included_label", "included_final", "included_flag", "include"]


def _read(path: Path) -> list[dict]:
    with path.open(newline="", encoding="utf-8-sig") as fh:
        first = fh.readline()
        fh.seek(0)
        dialect = "excel-tab" if path.suffix.lower() in (".tsv", ".tab") or "\t" in first else "excel"
        if dialect == "excel" and first.count(";") > first.count(","):
            reader = csv.DictReader(fh, delimiter=";")
        else:
            reader = csv.DictReader(fh, dialect=dialect)
        return [{(k or "").strip(): (v or "").strip() for k, v in r.items()} for r in reader]


def prior_labels(screening: list[dict]) -> dict[str, str]:
    """title_abstract consensus include -> 1, exclude -> 0; maybe/empty -> none."""
    out = {}
    for r in screening:
        if r.get("stage") != "title_abstract":
            continue
        c = r.get("consensus", "")
        if c == "include":
            out[r["record_id"]] = "1"
        elif c == "exclude":
            out[r["record_id"]] = "0"
    return out


def export_rows(library: list[dict], labels: dict[str, str] | None = None) -> list[dict]:
    rows, seen = [], set()
    for r in library:
        rid = r.get("record_id", "")
        if not rid:
            raise SystemExit("library row without record_id")
        if rid in seen:
            raise SystemExit(f"duplicate record_id {rid}")
        seen.add(rid)
        if not (r.get("title") or r.get("abstract")):
            raise SystemExit(f"{rid}: ASReview needs a title or an abstract")
        out = {c: r.get(c, "") for c in EXPORT_COLUMNS}
        out[ID_COLUMN] = rid
        out["included"] = (labels or {}).get(rid, "")
        rows.append(out)
    return rows


def _label(row: dict) -> str:
    for col in LABEL_COLUMNS:
        if col in row:
            val = row[col].strip().lower()
            if val in ("1", "1.0", "true"):
                return "1"
            if val in ("0", "0.0", "false"):
                return "0"
            return ""
    raise SystemExit("no label column (asreview_label) in ASReview export")


def import_rows(export: list[dict], screener: str | None = None):
    staged, counts = [], {"relevant": 0, "irrelevant": 0, "not_seen": 0}
    seen = set()
    for r in export:
        rid = r.get(ID_COLUMN, "")
        if not rid:
            raise SystemExit(f"ASReview export row without {ID_COLUMN}; was the file made by 'export'?")
        if rid in seen:
            raise SystemExit(f"duplicate {ID_COLUMN} {rid}")
        seen.add(rid)
        lab = _label(r)
        if lab == "":
            counts["not_seen"] += 1
            continue
        counts["relevant" if lab == "1" else "irrelevant"] += 1
        staged.append({
            "record_id": rid,
            "stage": "title_abstract",
            "screener": screener or r.get("asreview_user_name") or "asreview",
            "decision": "include" if lab == "1" else "exclude",
            "reason_code": "",
            "reason_note": r.get("asreview_note", ""),
            "date": r.get("asreview_time", "")[:10],
            "consensus": "",
        })
    counts["exclude_missing_reason_code"] = counts["irrelevant"]
    return staged, counts


def _write(path: Path, columns: list[str], rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=columns)
        w.writeheader()
        w.writerows(rows)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="[[TODO-TEXT: one-line -h description of asreview_io.py]]")
    sub = ap.add_subparsers(dest="cmd", required=True)
    ex = sub.add_parser("export", help="[[TODO-TEXT: help for export]]")
    ex.add_argument("library", type=Path, help="[[TODO-TEXT: help for library.csv]]")
    ex.add_argument("-o", "--out", type=Path, required=True, help="[[TODO-TEXT: help for export --out]]")
    ex.add_argument("--screening", type=Path, help="[[TODO-TEXT: help for --screening prior labels]]")
    im = sub.add_parser("import", help="[[TODO-TEXT: help for import]]")
    im.add_argument("asreview_export", type=Path, help="[[TODO-TEXT: help for ASReview export file]]")
    im.add_argument("-o", "--out", type=Path, required=True, help="[[TODO-TEXT: help for import --out staging file]]")
    im.add_argument("--screener", help="[[TODO-TEXT: help for --screener]]")
    args = ap.parse_args(argv)

    if args.cmd == "export":
        labels = prior_labels(_read(args.screening)) if args.screening else None
        rows = export_rows(_read(args.library), labels)
        _write(args.out, EXPORT_COLUMNS, rows)
        print(json.dumps({"out": str(args.out), "records": len(rows),
                          "prior_labels": sum(1 for r in rows if r["included"])}))
        return 0

    staged, counts = import_rows(_read(args.asreview_export), args.screener)
    _write(args.out, SCREENING_COLUMNS, staged)
    print(json.dumps({"out": str(args.out), **counts}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
