#!/usr/bin/env python3
"""Find legal open-access PDFs for a list of DOIs. No account or API key needed.

Input: any .tsv/.csv with a `doi` column (optional `record_id`, `title`), e.g.
03-screening/included.tsv, 02-records/library.csv, or a one-column DOI list.
Lookup order per DOI: OpenAlex (free, no key) -> Unpaywall (only when
LRS_CONTACT_EMAIL is set, because Unpaywall requires an email). Writes
oa_check.csv with one row per input row. With --download DIR it saves each
found OA PDF as DIR/<record_id or safe-doi>.pdf; it never overwrites a file.
Closed papers are listed as `closed` so the user can fetch them through their
library, interlibrary loan, or the author. No shadow libraries.
Exit 0 on success, 1 if any lookup errored (rows still written), 2 bad input.
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Callable, Optional, Sequence

UA = "literature-review-skills/find_oa_pdfs"
FIELDS = ["record_id", "doi", "title", "is_oa", "oa_status", "pdf_url",
          "landing_url", "source", "local_path", "note"]


def norm_doi(value: str) -> str:
    v = (value or "").strip()
    v = re.sub(r"^https?://(dx\.)?doi\.org/", "", v, flags=re.I)
    v = re.sub(r"^doi:\s*", "", v, flags=re.I)
    return v.strip().lower()


def http_json(url: str, timeout: int = 30) -> dict:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def openalex(doi: str, get: Callable[[str], dict]) -> dict:
    mail = os.environ.get("LRS_CONTACT_EMAIL", "")
    url = "https://api.openalex.org/works/doi:" + urllib.parse.quote(doi, safe="/")
    if mail:
        url += "?mailto=" + urllib.parse.quote(mail)
    data = get(url)
    oa = data.get("open_access") or {}
    best = data.get("best_oa_location") or {}
    return {"is_oa": bool(oa.get("is_oa")), "oa_status": oa.get("oa_status") or "",
            "pdf_url": best.get("pdf_url") or "",
            "landing_url": best.get("landing_page_url") or oa.get("oa_url") or "",
            "title": data.get("title") or ""}


def unpaywall(doi: str, get: Callable[[str], dict]) -> Optional[dict]:
    mail = os.environ.get("LRS_CONTACT_EMAIL", "")
    if not mail:
        return None
    data = get(f"https://api.unpaywall.org/v2/{urllib.parse.quote(doi, safe='/')}?email="
               + urllib.parse.quote(mail))
    best = data.get("best_oa_location") or {}
    return {"is_oa": bool(data.get("is_oa")), "oa_status": data.get("oa_status") or "",
            "pdf_url": best.get("url_for_pdf") or "", "landing_url": best.get("url") or "",
            "title": data.get("title") or ""}


def read_rows(path: Path) -> list[dict]:
    text = path.read_text(encoding="utf-8-sig")
    first = text.splitlines()[0] if text.strip() else ""
    if "doi" not in first.lower():  # bare DOI list, one per line
        return [{"doi": line.strip()} for line in text.splitlines() if line.strip()]
    delim = "\t" if "\t" in first else ","
    rows = list(csv.DictReader(text.splitlines(), delimiter=delim))
    return [{(k or "").strip().lower(): (v or "") for k, v in r.items()} for r in rows]


def safe_name(row: dict) -> str:
    base = row.get("record_id") or row["doi"]
    return re.sub(r"[^A-Za-z0-9._-]+", "_", base)[:120] + ".pdf"


def download(url: str, dest: Path, timeout: int = 60) -> str:
    if dest.exists():
        return "exists, not overwritten"
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        body = resp.read()
    if not body.startswith(b"%PDF"):
        return "link did not return a PDF; open landing_url in a browser"
    dest.write_bytes(body)
    return "saved"


def run(rows: list[dict], get=http_json, fetch=download, out_dir: Optional[Path] = None,
        pause: float = 0.2) -> tuple[list[dict], int]:
    out, errors = [], 0
    for row in rows:
        doi = norm_doi(row.get("doi", ""))
        rec = {k: "" for k in FIELDS}
        rec.update(record_id=row.get("record_id", ""), doi=doi, title=row.get("title", ""))
        if not doi:
            rec.update(oa_status="not_checked", note="no DOI; search the title in Google Scholar or ask the author")
            out.append(rec)
            continue
        hit = None
        for name, fn in (("openalex", openalex), ("unpaywall", unpaywall)):
            try:
                res = fn(doi, get)
            except Exception as exc:  # network, 404, JSON
                rec["note"] = (rec["note"] + f" {name} error: {exc}").strip()
                if "404" not in str(exc):
                    errors += 1
                continue
            if res is None:
                continue
            if hit is None or (res["pdf_url"] and not hit["pdf_url"]):
                hit, rec["source"] = res, name
            if hit["pdf_url"]:
                break
        if hit:
            rec.update(is_oa="yes" if hit["is_oa"] else "no",
                       oa_status=hit["oa_status"] or ("closed" if not hit["is_oa"] else ""),
                       pdf_url=hit["pdf_url"], landing_url=hit["landing_url"],
                       title=rec["title"] or hit["title"])
        elif not rec["oa_status"]:
            rec["oa_status"] = "not_checked"
        if out_dir and rec["pdf_url"]:
            dest = out_dir / safe_name(rec)
            try:
                status = fetch(rec["pdf_url"], dest)
            except Exception as exc:
                status = f"download failed: {exc}"
            if status in ("saved", "exists, not overwritten"):
                rec["local_path"] = str(dest)
            rec["note"] = (rec["note"] + " " + status).strip()
        out.append(rec)
        time.sleep(pause)
    return out, errors


def main(argv: Optional[Sequence[str]] = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("input", help="TSV/CSV with a doi column, or a plain DOI list")
    ap.add_argument("-o", "--out", default="oa_check.csv")
    ap.add_argument("--download", metavar="DIR", help="save found OA PDFs here")
    args = ap.parse_args(argv)
    try:
        rows = read_rows(Path(args.input))
    except (OSError, UnicodeDecodeError, IndexError) as exc:
        print(f"ERROR {exc}", file=sys.stderr)
        return 2
    out_dir = Path(args.download) if args.download else None
    if out_dir:
        out_dir.mkdir(parents=True, exist_ok=True)
    result, errors = run(rows, out_dir=out_dir)
    with open(args.out, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(result)
    n_pdf = sum(1 for r in result if r["pdf_url"])
    n_closed = sum(1 for r in result if r["is_oa"] == "no")
    print(f"rows={len(result)} oa_pdf_found={n_pdf} closed={n_closed} "
          f"saved={sum(1 for r in result if r['local_path'])} lookup_errors={errors} -> {args.out}")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
