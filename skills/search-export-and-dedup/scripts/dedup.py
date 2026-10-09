#!/usr/bin/env python3
"""Deduplicate literature search exports (RIS, PubMed NBIB, CSV).

Match priority is DOI, then PMID, then normalized title+year.
A lower-priority key never merges two records that disagree on a
higher-priority identifier when both records have that identifier.

Writes library.csv (one row per kept record) and prisma_counts.json.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from pathlib import Path


COLUMNS = [
    "record_id",
    "title",
    "year",
    "authors",
    "journal",
    "doi",
    "pmid",
    "abstract",
    "sources",
    "n_copies",
    "identity_key",
]

_DOI_RE = re.compile(r"(10\.\d{4,}/\S+)", re.IGNORECASE)
_YEAR_RE = re.compile(r"\b(?:1[6-9]\d{2}|20\d{2})\b")
_RIS_TAG = re.compile(r"^([A-Z0-9]{2})\s+-\s?(.*)$")
_NBIB_TAG = re.compile(r"^([A-Z][A-Z0-9]{1,3})\s*-\s?(.*)$")

_HEADER_MAP = {
    "doi": "doi",
    "do": "doi",
    "di": "doi",
    "pmid": "pmid",
    "pubmed": "pmid",
    "pubmed id": "pmid",
    "pubmed_id": "pmid",
    "pmid id": "pmid",
    "title": "title",
    "ti": "title",
    "article title": "title",
    "document title": "title",
    "year": "year",
    "py": "year",
    "publication year": "year",
    "pubyear": "year",
    "date": "year",
    "authors": "authors",
    "author": "authors",
    "au": "authors",
    "author full names": "authors",
    "abstract": "abstract",
    "ab": "abstract",
    "journal": "journal",
    "source title": "journal",
    "publication name": "journal",
    "journal title": "journal",
    "so": "journal",
}


def normalize_doi(value: str) -> str:
    """Lowercase a DOI and strip URL or doi: prefixes."""
    if value is None:
        return ""
    text = str(value).strip().lstrip("\ufeff")
    if not text:
        return ""
    text = re.sub(r"^https?://(?:dx\.)?doi\.org/", "", text, flags=re.IGNORECASE)
    text = re.sub(r"^doi:\s*", "", text, flags=re.IGNORECASE)
    text = text.strip().strip("<>")
    match = _DOI_RE.search(text)
    if not match:
        return ""
    doi = match.group(1)
    doi = re.sub(r"\[.*$", "", doi)
    doi = doi.rstrip(".,;")
    return doi.lower()


def normalize_pmid(value: str) -> str:
    """Return a PMID as digits, or empty if the value is not a PMID."""
    if value is None:
        return ""
    text = str(value).strip()
    if not text:
        return ""
    if re.fullmatch(r"\d+\.0+", text):
        text = text.split(".", 1)[0]
    labeled = re.search(r"\bPMID[:\s]*([0-9]{1,9})\b", text, flags=re.IGNORECASE)
    if labeled:
        return str(int(labeled.group(1)))
    url = re.search(r"pubmed\.ncbi\.nlm\.nih\.gov/([0-9]{1,9})", text, flags=re.IGNORECASE)
    if url:
        return str(int(url.group(1)))
    if re.fullmatch(r"[0-9]{1,9}", text):
        return str(int(text))
    return ""


def normalize_title(value: str) -> str:
    """Lowercase a title and treat punctuation as a word break."""
    if not value:
        return ""
    text = str(value).lower()
    text = re.sub(r"[^\w\s]", " ", text, flags=re.UNICODE)
    return re.sub(r"\s+", " ", text).strip()


def extract_year(value: str) -> str:
    if value is None:
        return ""
    match = _YEAR_RE.search(str(value))
    return match.group(0) if match else ""


def title_year_key(title: str, year: str) -> str:
    norm = normalize_title(title)
    if not norm or not year:
        return ""
    return norm + "|" + year


def new_record() -> dict:
    return {
        "source": "",
        "source_file": "",
        "title": "",
        "year": "",
        "authors": "",
        "journal": "",
        "doi": "",
        "pmid": "",
        "abstract": "",
    }


def normalize_record(rec: dict) -> dict:
    out = new_record()
    out.update(rec)
    out["title"] = str(out.get("title") or "").strip()
    out["authors"] = str(out.get("authors") or "").strip()
    out["journal"] = str(out.get("journal") or "").strip()
    out["abstract"] = str(out.get("abstract") or "").strip()
    out["doi"] = normalize_doi(out.get("doi") or "")
    out["pmid"] = normalize_pmid(out.get("pmid") or "")
    out["year"] = extract_year(out.get("year") or "")
    out["source"] = str(out.get("source") or "").strip()
    out["source_file"] = str(out.get("source_file") or "").strip()
    return out


def _append_author(rec: dict, value: str) -> None:
    value = value.strip()
    if not value:
        return
    if rec["authors"]:
        rec["authors"] = rec["authors"] + "; " + value
    else:
        rec["authors"] = value


def _apply_doi(rec: dict, value: str) -> None:
    doi = normalize_doi(value)
    if doi and not rec["doi"]:
        rec["doi"] = doi


def parse_ris(text: str) -> list:
    records = []
    current = None
    last_tag = None

    def finish() -> None:
        nonlocal current, last_tag
        if current and (current["title"] or current["doi"] or current["pmid"]):
            records.append(current)
        current = None
        last_tag = None

    for raw in text.splitlines():
        line = raw.rstrip("\r").lstrip("\ufeff")
        match = _RIS_TAG.match(line)
        if not match:
            if current is not None and line.startswith((" ", "\t")) and last_tag:
                extra = line.strip()
                if last_tag in {"TI", "T1", "ST", "CT"} and extra:
                    current["title"] = (current["title"] + " " + extra).strip()
                elif last_tag == "AB" and extra:
                    current["abstract"] = (current["abstract"] + " " + extra).strip()
            continue
        tag = match.group(1).upper()
        val = match.group(2).strip()
        if tag == "TY":
            if current is not None:
                finish()
            current = new_record()
            last_tag = tag
            continue
        if current is None:
            current = new_record()
        if tag == "ER":
            finish()
            continue
        last_tag = tag
        if tag == "TI":
            current["title"] = val
        elif tag in {"T1", "ST", "CT"} and not current["title"]:
            current["title"] = val
        elif tag == "AB":
            current["abstract"] = val
        elif tag in {"AU", "A1"}:
            _append_author(current, val)
        elif tag in {"PY", "Y1", "DA"} and not current["year"]:
            current["year"] = extract_year(val)
        elif tag in {"DO", "DI", "DOI"} or tag == "M3":
            _apply_doi(current, val)
        elif tag in {"AN", "ID"} and not current["pmid"]:
            current["pmid"] = normalize_pmid(val)
        elif tag == "N1" and not current["pmid"]:
            current["pmid"] = normalize_pmid(val)
        elif tag == "UR" and not current["pmid"]:
            current["pmid"] = normalize_pmid(val)
        elif tag in {"JO", "JF", "JA", "T2"} and not current["journal"]:
            current["journal"] = val
    if current is not None:
        finish()
    return records


def parse_nbib(text: str) -> list:
    records = []
    current = None
    last_tag = None

    def finish() -> None:
        nonlocal current, last_tag
        if current and (current["title"] or current["doi"] or current["pmid"]):
            records.append(current)
        current = None
        last_tag = None

    for raw in text.splitlines():
        line = raw.rstrip("\r").lstrip("\ufeff")
        if line.startswith("      ") and current is not None and last_tag:
            extra = line.strip()
            if not extra:
                continue
            if last_tag == "TI":
                current["title"] = (current["title"] + " " + extra).strip()
            elif last_tag == "AB":
                current["abstract"] = (current["abstract"] + " " + extra).strip()
            continue
        match = _NBIB_TAG.match(line)
        if not match:
            continue
        tag = match.group(1).upper()
        val = match.group(2).strip()
        if tag == "PMID":
            if current is not None:
                finish()
            current = new_record()
            current["pmid"] = normalize_pmid(val)
            last_tag = tag
            continue
        if current is None:
            current = new_record()
        last_tag = tag
        if tag == "TI":
            current["title"] = val
        elif tag == "AB":
            current["abstract"] = val
        elif tag == "DP" and not current["year"]:
            current["year"] = extract_year(val)
        elif tag in {"AID", "LID"}:
            if re.search(r"\[doi\]", val, flags=re.IGNORECASE) or val.lower().startswith("10."):
                _apply_doi(current, val)
        elif tag in {"AU", "FAU"}:
            _append_author(current, val)
        elif tag == "JT" and not current["journal"]:
            current["journal"] = val
    if current is not None:
        finish()
    return records


def _map_csv_row(row: dict) -> dict:
    rec = new_record()
    for key, value in row.items():
        if key is None:
            continue
        header = " ".join(str(key).replace("\ufeff", "").strip().lower().split())
        field = _HEADER_MAP.get(header)
        if not field:
            continue
        text = "" if value is None else str(value).strip()
        if field == "doi":
            _apply_doi(rec, text)
        elif field == "pmid" and not rec["pmid"]:
            rec["pmid"] = normalize_pmid(text)
        elif field == "year" and not rec["year"]:
            rec["year"] = extract_year(text)
        elif field == "authors":
            rec["authors"] = text
        elif field == "title":
            rec["title"] = text
        elif field == "abstract":
            rec["abstract"] = text
        elif field == "journal":
            rec["journal"] = text
    return rec


def read_csv_stdlib(path: Path) -> list:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        return [_map_csv_row(row) for row in reader]


def read_csv_pandas(path: Path) -> list:
    import pandas as pd

    frame = pd.read_csv(path, dtype=str, keep_default_na=False, encoding="utf-8-sig")
    rows = frame.to_dict(orient="records")
    return [_map_csv_row(row) for row in rows]


def load_pandas():
    """Return pandas, or None when it is missing or cannot be imported."""
    try:
        import pandas as pd
    except Exception:
        return None
    return pd


def read_csv_rows(path: Path, use_pandas: bool | None = None) -> list:
    if use_pandas is False:
        return read_csv_stdlib(path)
    pandas_module = load_pandas()
    if pandas_module is None:
        if use_pandas is True:
            raise ValueError("pandas was requested but is not importable")
        return read_csv_stdlib(path)
    return read_csv_pandas(path)


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8-sig")
    except UnicodeDecodeError as exc:
        raise ValueError("%s is not UTF-8; re-export the file as UTF-8" % path) from exc


def detect_format(path: Path, text: str) -> str:
    ext = path.suffix.lower()
    if ext == ".ris":
        return "ris"
    if ext in {".nbib", ".medline"}:
        return "nbib"
    if ext == ".csv":
        return "csv"
    head = "\n".join(text.splitlines()[:40])
    if re.search(r"(?m)^PMID\s*-", head) and re.search(r"(?m)^TI\s*-", head):
        return "nbib"
    if re.search(r"(?m)^TY\s+-", head):
        return "ris"
    first = head.splitlines()[0] if head.splitlines() else ""
    if "," in first:
        return "csv"
    raise ValueError("cannot detect format for %s" % path)


def parse_file(path: Path, source: str, use_pandas: bool | None = None) -> list:
    path = Path(path)
    if path.suffix.lower() == ".csv":
        records = read_csv_rows(path, use_pandas=use_pandas)
    else:
        text = read_text(path)
        kind = detect_format(path, text)
        if kind == "csv":
            records = read_csv_rows(path, use_pandas=use_pandas)
        elif kind == "nbib":
            records = parse_nbib(text)
        else:
            records = parse_ris(text)
    named = path.name
    usable = []
    for rec in records:
        rec["source"] = source
        rec["source_file"] = named
        rec = normalize_record(rec)
        if rec["doi"] or rec["pmid"] or rec["title"]:
            usable.append(rec)
    return usable


def _conflicts(left: dict, right: dict, field: str) -> bool:
    return bool(left.get(field) and right.get(field) and left[field] != right[field])


def _identity_key(rec: dict) -> str:
    if rec.get("doi"):
        return "doi"
    if rec.get("pmid"):
        return "pmid"
    if title_year_key(rec.get("title", ""), rec.get("year", "")):
        return "title_year"
    return "none"


def _index_cluster(item: dict, idx: int, doi_index: dict, pmid_index: dict, ty_index: dict) -> None:
    if item["doi"] and item["doi"] not in doi_index:
        doi_index[item["doi"]] = idx
    if item["pmid"] and item["pmid"] not in pmid_index:
        pmid_index[item["pmid"]] = idx
    key = title_year_key(item["title"], item["year"])
    if key and key not in ty_index:
        ty_index[key] = idx


def _find_match(rec: dict, canonical: list, doi_index: dict, pmid_index: dict, ty_index: dict):
    if rec["doi"] and rec["doi"] in doi_index:
        return doi_index[rec["doi"]], "doi"
    if rec["pmid"] and rec["pmid"] in pmid_index:
        other = canonical[pmid_index[rec["pmid"]]]
        if not _conflicts(rec, other, "doi"):
            return pmid_index[rec["pmid"]], "pmid"
    key = title_year_key(rec["title"], rec["year"])
    if key and key in ty_index:
        other = canonical[ty_index[key]]
        if not _conflicts(rec, other, "doi") and not _conflicts(rec, other, "pmid"):
            return ty_index[key], "title_year"
    return None, ""


def _merge(item: dict, rec: dict) -> None:
    item["n_copies"] += 1
    source = rec.get("source") or ""
    if source and source not in item["sources"]:
        item["sources"].append(source)
    for field in ("doi", "pmid", "title", "year", "journal"):
        if not item[field] and rec[field]:
            item[field] = rec[field]
    for field in ("authors", "abstract"):
        if rec[field] and len(rec[field]) > len(item[field]):
            item[field] = rec[field]
    item["identity_key"] = _identity_key(item)


def deduplicate(records: list) -> tuple:
    """Return (clusters, removed_by_key) for already parsed records."""
    canonical = []
    doi_index = {}
    pmid_index = {}
    ty_index = {}
    removed = {"doi": 0, "pmid": 0, "title_year": 0}
    for raw in records:
        rec = normalize_record(raw)
        if not (rec["doi"] or rec["pmid"] or rec["title"]):
            continue
        idx, how = _find_match(rec, canonical, doi_index, pmid_index, ty_index)
        if idx is None:
            item = {
                "title": rec["title"],
                "year": rec["year"],
                "authors": rec["authors"],
                "journal": rec["journal"],
                "doi": rec["doi"],
                "pmid": rec["pmid"],
                "abstract": rec["abstract"],
                "sources": [rec["source"]] if rec["source"] else [],
                "n_copies": 1,
                "identity_key": _identity_key(rec),
            }
            canonical.append(item)
            _index_cluster(item, len(canonical) - 1, doi_index, pmid_index, ty_index)
        else:
            removed[how] += 1
            _merge(canonical[idx], rec)
            _index_cluster(canonical[idx], idx, doi_index, pmid_index, ty_index)
    return canonical, removed


def tally_sources(records: list) -> dict:
    by_source = {}
    for rec in records:
        src = rec.get("source") or "unspecified"
        slot = by_source.setdefault(src, {"records_exported": 0, "files": []})
        slot["records_exported"] += 1
        name = rec.get("source_file") or ""
        if name and name not in slot["files"]:
            slot["files"].append(name)
    return dict(sorted(by_source.items()))


def summarize(records: list) -> dict:
    usable = []
    skipped = 0
    for raw in records:
        rec = normalize_record(raw)
        if rec["doi"] or rec["pmid"] or rec["title"]:
            usable.append(rec)
        else:
            skipped += 1
    clusters, removed = deduplicate(usable)
    removed_n = sum(removed.values())
    payload = {
        "by_source": tally_sources(usable),
        "identified_total": len(usable),
        "skipped_without_identifier": skipped,
        "duplicates_removed": removed_n,
        "duplicates_removed_by_key": removed,
        "records_after_deduplication": len(clusters),
    }
    return payload, clusters


def write_outputs(out_dir: Path, payload: dict, clusters: list) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    library = out_dir / "library.csv"
    counts = out_dir / "prisma_counts.json"
    with library.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=COLUMNS, lineterminator="\n")
        writer.writeheader()
        for number, item in enumerate(clusters, start=1):
            writer.writerow(
                {
                    "record_id": "R%04d" % number,
                    "title": item["title"],
                    "year": item["year"],
                    "authors": item["authors"],
                    "journal": item["journal"],
                    "doi": item["doi"],
                    "pmid": item["pmid"],
                    "abstract": item["abstract"],
                    "sources": ";".join(item["sources"]),
                    "n_copies": item["n_copies"],
                    "identity_key": item["identity_key"],
                }
            )
    counts.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def collect_inputs(inputs: list, sources: list, use_pandas: bool | None = None) -> list:
    if sources and len(sources) != len(inputs):
        raise ValueError("--source must be given once per --input, or omitted")
    records = []
    for index, raw_path in enumerate(inputs):
        path = Path(raw_path)
        if not path.is_file():
            raise ValueError("input not found: %s" % path)
        if sources:
            source = sources[index].strip()
        else:
            source = path.stem.lower()
        if not source:
            raise ValueError("empty --source for %s" % path)
        found = parse_file(path, source, use_pandas=use_pandas)
        if not found:
            raise ValueError("no records parsed from %s" % path)
        records.extend(found)
    return records


def main(argv: list | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Deduplicate RIS, PubMed NBIB, and CSV literature exports."
    )
    parser.add_argument("--input", action="append", required=True, help="Export file (.ris, .nbib, .txt, .csv)")
    parser.add_argument("--source", action="append", help="Source label, one per --input (for example pubmed)")
    parser.add_argument("--out-dir", required=True, help="Directory for library.csv and prisma_counts.json")
    parser.add_argument(
        "--use-pandas",
        choices=("auto", "yes", "no"),
        default="auto",
        help="CSV reader. auto uses pandas when it is installed (default: auto)",
    )
    args = parser.parse_args(argv)
    pandas_flag = {"auto": None, "yes": True, "no": False}[args.use_pandas]
    try:
        records = collect_inputs(args.input, args.source or [], use_pandas=pandas_flag)
        payload, clusters = summarize(records)
        write_outputs(Path(args.out_dir), payload, clusters)
    except ValueError as exc:
        print("error: %s" % exc, file=sys.stderr)
        return 1
    print(
        "wrote %d records (%d duplicates removed) to %s"
        % (payload["records_after_deduplication"], payload["duplicates_removed"], args.out_dir)
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
