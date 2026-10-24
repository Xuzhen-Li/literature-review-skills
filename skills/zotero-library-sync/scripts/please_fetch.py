#!/usr/bin/env python3
"""Build the short "please fetch" list: the only papers the human is asked for.

A paper goes on the list only when all three hold:
  1. the agent marked it essential in 04-library/fulltext_need.tsv,
  2. it needs the full text (need=essential means exactly that), and
  3. the agent could not get it (no local_path in the status file and no
     PDF at 04-library/uploads/<stem>.pdf, where <stem> is the record_id,
     or for a plain DOI list the sanitized DOI plus a short hash, e.g.
     10.1000_x_y-1a2b3c4d; a file counts only if it starts with %PDF-).

Inputs
  --status  oa_check.csv from find_oa_pdfs.py (or pdf_status.csv): record_id,
            doi, title, local_path, landing_url, pdf_url (an OA link whose download
            failed is shown so the user can try it in a browser first)
  --need    fulltext_need.tsv written by the agent: record_id, doi, need,
            why, rank. need is essential | useful | abstract_ok; rank is 1 for
            the most important paper.
Outputs (in --out-dir, default 04-library). These three files are generated:
every run rewrites them from the inputs, so never hand-edit them; edit
fulltext_need.tsv and rerun instead.
  please_fetch.md   numbered list for the human: DOI, title, why it matters,
                    where to save the PDF
  please_fetch.tsv  the same rows for scripts
  abstract_only.tsv missing papers the review will use from the abstract only,
                    to report as a limitation
Exit 0 when written; 2 on bad input, including a missing paper with no row in
fulltext_need.tsv (it is listed so the agent triages it first).
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import re
import sys
from pathlib import Path
from typing import Optional, Sequence

NEEDS = ("essential", "useful", "abstract_ok")
TSV_FIELDS = ["priority", "record_id", "doi", "title", "why", "save_as", "landing_url", "pdf_url"]
ABS_FIELDS = ["record_id", "doi", "title", "need", "why"]


def _read(path: Path) -> list[dict]:
    with path.open(newline="", encoding="utf-8-sig") as fh:
        first = fh.readline()
        fh.seek(0)
        rdr = csv.DictReader(fh, delimiter="\t" if "\t" in first else ",")
        if not rdr.fieldnames:
            raise ValueError(f"{path} has no header")
        return [{(k or "").strip().lower(): (v or "").strip() for k, v in r.items() if k} for r in rdr]


def _doi(v: str) -> str:
    v = re.sub(r"^https?://(dx\.)?doi\.org/", "", (v or "").strip(), flags=re.I)
    return re.sub(r"^doi:\s*", "", v, flags=re.I).lower()


def _key(row: dict) -> str:
    return row.get("record_id") or _doi(row.get("doi", ""))


def upload_stem(record_id: str, doi: str) -> str:
    """File stem the user saves an upload under: record_id, else sanitized DOI + hash."""
    if record_id:
        return record_id
    d = _doi(doi)
    if not d:
        return ""
    base = re.sub(r"[^A-Za-z0-9._-]+", "_", d)[:80]
    return f"{base}-{hashlib.sha1(d.encode('utf-8')).hexdigest()[:8]}"


def _is_pdf(p: Path) -> bool:
    try:
        with p.open("rb") as fh:
            return fh.read(5) == b"%PDF-"
    except OSError:
        return False


def build(status: list[dict], need: list[dict], uploads: Optional[Path], max_n: int):
    """Return (fetch_rows, abstract_rows, untriaged, overflow)."""
    triage = {}
    for r in need:
        n = r.get("need", "").lower()
        if n not in NEEDS:
            raise ValueError(f"need must be one of {', '.join(NEEDS)}: {_key(r) or r}")
        triage[_key(r)] = r
        if r.get("doi"):
            triage.setdefault(_doi(r["doi"]), r)
    missing = []
    for r in status:
        stem = upload_stem(r.get("record_id", ""), r.get("doi", ""))
        have = bool(r.get("local_path")) or (uploads is not None and bool(stem) and _is_pdf(uploads / f"{stem}.pdf"))
        if not have:
            missing.append(r)
    fetch, abstract, untriaged = [], [], []
    for r in missing:
        t = triage.get(r.get("record_id", "")) or triage.get(_doi(r.get("doi", "")))
        if t is None:
            untriaged.append(_key(r) or r.get("title", "?"))
            continue
        row = {"record_id": r.get("record_id", "") or t.get("record_id", ""),
               "doi": _doi(r.get("doi") or t.get("doi", "")), "title": r.get("title", ""),
               "why": t.get("why", ""), "need": t["need"].lower(), "landing_url": r.get("landing_url", ""), "pdf_url": r.get("pdf_url", ""),
               "_stem": upload_stem(r.get("record_id", ""), r.get("doi") or t.get("doi", ""))}
        if row["need"] == "essential":
            try:
                row["_rank"] = float(t.get("rank") or "inf")
            except ValueError:
                raise ValueError(f"rank is not a number for {_key(row)}: {t.get('rank')}")
            if not row["why"]:
                raise ValueError(f"essential paper needs a why: {_key(row)}")
            fetch.append(row)
        else:
            abstract.append(row)
    fetch.sort(key=lambda x: (x["_rank"], x["record_id"]))
    overflow = fetch[max_n:]
    fetch = fetch[:max_n]
    for i, row in enumerate(fetch, 1):
        row["priority"] = i
        row["save_as"] = f"04-library/uploads/{row['_stem']}.pdf" if row["_stem"] else "(no DOI or record_id; ask the agent for a file name)"
    for row in overflow:  # over the cap: the review proceeds on the abstract
        row["need"] = "essential_over_cap"
        abstract.append(row)
    return fetch, abstract, untriaged, overflow


def render_md(fetch: list[dict], n_missing_abstract: int) -> str:
    if not fetch:
        return ("# Please fetch\n\nNothing to fetch. Every paper the review needs in full text was "
                "downloaded from an open-access source.\n")
    lines = ["# Please fetch", "",
             f"I could not get these {len(fetch)} papers from any free source, and the review needs their "
             "full text. They are listed from most to least important. Please download what you can through "
             "your library, interlibrary loan, or from the authors, and save each PDF under the file name "
             "shown. Skip any you cannot get; I will rely on the abstract and note this in the limitations.", ""]
    for r in fetch:
        lines.append(f"{r['priority']}. https://doi.org/{r['doi']}" if r["doi"] else f"{r['priority']}. (no DOI)")
        if r["title"]:
            lines.append(f"   {r['title']}")
        lines.append(f"   Why: {r['why']}")
        if r.get("pdf_url"):
            lines.append(f"   Open-access link that refused my download (try it in your browser first): {r['pdf_url']}")
        lines.append(f"   Save as: {r['save_as']}")
        lines.append("")
    if n_missing_abstract:
        lines.append(f"{n_missing_abstract} other papers without a free PDF will be used from the abstract "
                     "(04-library/abstract_only.tsv). You do not need to fetch them.")
    return "\n".join(lines).rstrip() + "\n"


def _write(path: Path, fields, rows):
    with path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=fields, delimiter="\t", extrasaction="ignore", lineterminator="\n")
        w.writeheader()
        w.writerows(rows)


def main(argv: Optional[Sequence[str]] = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--status", required=True, type=Path)
    ap.add_argument("--need", required=True, type=Path)
    ap.add_argument("--uploads", type=Path, help="folder with PDFs the user already saved (04-library/uploads)")
    ap.add_argument("--out-dir", type=Path, default=Path("04-library"))
    ap.add_argument("--max", type=int, default=15, help="longest list to hand the human (default 15)")
    args = ap.parse_args(argv)
    try:
        fetch, abstract, untriaged, overflow = build(_read(args.status), _read(args.need), args.uploads, args.max)
    except (OSError, ValueError) as exc:
        print(f"ERROR {exc}", file=sys.stderr)
        return 2
    if untriaged:
        print("ERROR no row in fulltext_need.tsv for missing paper(s): " + ", ".join(untriaged), file=sys.stderr)
        return 2
    args.out_dir.mkdir(parents=True, exist_ok=True)
    _write(args.out_dir / "please_fetch.tsv", TSV_FIELDS, fetch)
    _write(args.out_dir / "abstract_only.tsv", ABS_FIELDS, abstract)
    (args.out_dir / "please_fetch.md").write_text(render_md(fetch, len(abstract)), encoding="utf-8")
    msg = f"OK please_fetch={len(fetch)} abstract_only={len(abstract)}"
    if overflow:
        msg += f" (over --max {args.max}: {len(overflow)} essential papers moved to abstract_only; tighten the ranking)"
    print(msg)
    return 0


if __name__ == "__main__":
    sys.exit(main())
