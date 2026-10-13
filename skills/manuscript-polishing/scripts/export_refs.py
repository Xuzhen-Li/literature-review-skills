#!/usr/bin/env python3
"""Export a records table to BibTeX (refs.bib) and CSL-JSON (refs.json).

Input: 03-screening/included.tsv, 02-records/library.csv, or any CSV/TSV
with title/year/doi/pmid and either authors or first_author. When the
input lacks full author lists, --library supplies them by record_id.

Citation keys: the citation_key column is used as-is when present.
Otherwise the key is the first author's ASCII family name plus the
four-digit year, with a, b, c... on collisions (the included.tsv rule).
Nothing is looked up online and nothing missing is invented: empty
fields are omitted, and rows without a title are skipped and reported.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
import unicodedata
from pathlib import Path

_YEAR = re.compile(r"\b(1[6-9]\d{2}|20\d{2})\b")
_BIB_SPECIAL = {
    "\\": r"\textbackslash{}",
    "{": r"\{",
    "}": r"\}",
    "&": r"\&",
    "%": r"\%",
    "$": r"\$",
    "#": r"\#",
    "_": r"\_",
    "~": r"\textasciitilde{}",
    "^": r"\textasciicircum{}",
}


def read_table(path: Path) -> list[dict]:
    with path.open(newline="", encoding="utf-8-sig") as fh:
        first = fh.readline()
        fh.seek(0)
        dialect = "excel-tab" if path.suffix.lower() in (".tsv", ".tab") or "\t" in first else "excel"
        reader = csv.DictReader(fh, dialect=dialect)
        return [{(k or "").strip().lower(): (v or "").strip() for k, v in r.items()} for r in reader]


def normalize_doi(value: str) -> str:
    text = re.sub(r"^https?://(?:dx\.)?doi\.org/", "", (value or "").strip(), flags=re.I)
    return re.sub(r"^doi:\s*", "", text, flags=re.I).rstrip(".").lower()


def split_authors(value: str) -> list[str]:
    return [a.strip() for a in (value or "").split(";") if a.strip()]


def parse_name(name: str) -> dict:
    """'Family, Given' / 'Family GI' -> CSL name; anything else -> literal."""
    name = name.strip()
    if "," in name:
        family, given = (p.strip() for p in name.split(",", 1))
        return {"family": family, "given": given} if given else {"family": family}
    parts = name.split()
    if len(parts) > 1 and re.fullmatch(r"[A-Z]{1,3}", parts[-1]):
        return {"family": " ".join(parts[:-1]), "given": " ".join(f"{c}." for c in parts[-1])}
    if len(parts) == 1:
        return {"family": parts[0]}
    return {"literal": name}


def ascii_letters(text: str) -> str:
    text = unicodedata.normalize("NFKD", text)
    return "".join(ch for ch in text if ch.isascii() and ch.isalpha())


def year_of(value: str) -> str:
    m = _YEAR.search(value or "")
    return m.group(1) if m else ""


def make_keys(records: list[dict]) -> None:
    taken = {r["citation_key"] for r in records if r.get("citation_key")}
    base_count: dict[str, int] = {}
    for r in records:
        if r.get("citation_key"):
            continue
        names = r["authors_parsed"]
        fam = names[0].get("family") or names[0].get("literal", "") if names else ""
        base = (ascii_letters(fam) or "Anon") + (r["year"] or "nd")
        base = base[0].upper() + base[1:]
        n = base_count.get(base, 0)
        key = base
        while key in taken:
            key = base + "abcdefghijklmnopqrstuvwxyz"[n % 26] * (n // 26 + 1)
            n += 1
        base_count[base] = n
        taken.add(key)
        r["citation_key"] = key


def build_records(rows: list[dict], library: dict[str, dict] | None = None):
    records, skipped = [], []
    for i, row in enumerate(rows, start=2):
        lib = (library or {}).get(row.get("record_id", ""), {})
        merged = {**lib, **{k: v for k, v in row.items() if v}}
        title = merged.get("title", "")
        rid = merged.get("record_id") or merged.get("citation_key") or f"row{i}"
        if not title:
            skipped.append(rid)
            continue
        authors = split_authors(merged.get("authors", ""))
        if not authors and merged.get("first_author"):
            authors = [merged["first_author"]]
        records.append({
            "record_id": merged.get("record_id", ""),
            "citation_key": merged.get("citation_key", ""),
            "title": title,
            "year": year_of(merged.get("year", "")),
            "authors_parsed": [parse_name(a) for a in authors],
            "authors_complete": bool(split_authors(merged.get("authors", ""))) or merged.get("n_authors") == "1",
            "journal": merged.get("journal") or merged.get("venue", ""),
            "doi": normalize_doi(merged.get("doi", "")),
            "pmid": re.sub(r"\.0$", "", merged.get("pmid", "")),
            "abstract": merged.get("abstract", ""),
        })
    make_keys(records)
    keys = [r["citation_key"] for r in records]
    dupes = sorted({k for k in keys if keys.count(k) > 1})
    if dupes:
        raise SystemExit(f"duplicate citation_key values: {', '.join(dupes)}")
    return records, skipped


def bib_escape(text: str) -> str:
    return "".join(_BIB_SPECIAL.get(ch, ch) for ch in text)


def bib_name(n: dict) -> str:
    if "literal" in n:
        return "{" + bib_escape(n["literal"]) + "}"
    return bib_escape(n["family"]) + (", " + bib_escape(n["given"]) if n.get("given") else "")


def to_bibtex(records: list[dict], with_abstract: bool = False) -> str:
    out = []
    for r in records:
        fields = [("title", bib_escape(r["title"]))]
        if r["authors_parsed"]:
            names = " and ".join(bib_name(n) for n in r["authors_parsed"])
            if not r["authors_complete"]:
                names += " and others"
            fields.append(("author", names))
        for key, val in (("journal", r["journal"]), ("year", r["year"])):
            if val:
                fields.append((key, bib_escape(val)))
        if r["doi"]:
            fields.append(("doi", r["doi"].replace("{", "").replace("}", "")))
        if r["pmid"]:
            fields.append(("pmid", r["pmid"]))
        if with_abstract and r["abstract"]:
            fields.append(("abstract", bib_escape(r["abstract"])))
        body = ",\n".join(f"  {k} = {{{v}}}" for k, v in fields)
        out.append(f"@article{{{r['citation_key']},\n{body}\n}}\n")
    return "\n".join(out)


def to_csl(records: list[dict], with_abstract: bool = False) -> list[dict]:
    items = []
    for r in records:
        item = {"id": r["citation_key"], "citation-key": r["citation_key"],
                "type": "article-journal", "title": r["title"]}
        if r["authors_parsed"]:
            item["author"] = r["authors_parsed"]
        if r["year"]:
            item["issued"] = {"date-parts": [[int(r["year"])]]}
        if r["journal"]:
            item["container-title"] = r["journal"]
        if r["doi"]:
            item["DOI"] = r["doi"]
        if r["pmid"]:
            item["PMID"] = r["pmid"]
        if with_abstract and r["abstract"]:
            item["abstract"] = r["abstract"]
        items.append(item)
    return items


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Exports a records table to BibTeX and CSL-JSON reference files.")
    ap.add_argument("table", type=Path, help="The input CSV or TSV spreadsheet file containing the records.")
    ap.add_argument("--library", type=Path, help="Optional path to the main library CSV file to fill missing fields like the full authors list.")
    ap.add_argument("--bib", type=Path, help="The output BibTeX file path, which defaults to refs.bib in the same folder as the input table.")
    ap.add_argument("--csl", type=Path, help="The output CSL-JSON file path, which defaults to refs.json in the same folder as the input table.")
    ap.add_argument("--with-abstract", action="store_true", help="Adds the abstract field to the exported files.")
    args = ap.parse_args(argv)

    rows = read_table(args.table)
    library = None
    if args.library:
        library = {r["record_id"]: r for r in read_table(args.library) if r.get("record_id")}
    records, skipped = build_records(rows, library)
    bib = args.bib or args.table.parent / "refs.bib"
    csl = args.csl or args.table.parent / "refs.json"
    bib.write_text(to_bibtex(records, args.with_abstract), encoding="utf-8")
    csl.write_text(json.dumps(to_csl(records, args.with_abstract), ensure_ascii=False, indent=2) + "\n",
                   encoding="utf-8")
    incomplete = [r["citation_key"] for r in records if not r["authors_complete"]]
    print(json.dumps({"bib": str(bib), "csl": str(csl), "exported": len(records),
                      "skipped_no_title": skipped, "authors_incomplete": incomplete}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
