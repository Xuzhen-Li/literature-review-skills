#!/usr/bin/env python3
"""Find legal open-access PDFs for a list of DOIs. No account or API key needed.

Input: any .tsv/.csv with a `doi` column (optional `record_id`, `title`), e.g.
03-screening/included.tsv, 02-records/library.csv, or a plain list with one
DOI (or https://doi.org/ URL) per line.
Lookup order per DOI: OpenAlex (free, no key) -> Unpaywall (only when
LRS_CONTACT_EMAIL is set, because Unpaywall requires an email). Writes
oa_check.csv with one row per input row (refuses to overwrite without --force).
With --download DIR it saves each found OA PDF (http/https only, size-capped)
as DIR/<record_id or doi>-<hash>.pdf; it never overwrites a file.
Closed papers are listed as `closed` so the user can fetch them through their
library, interlibrary loan, or the author. No shadow libraries.
Exit 0 on success; 1 if a lookup errored, a DOI row stayed not_checked, or a
download failed (rows are still written); 2 on bad input or existing output.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Callable, Optional, Sequence

UA = "literature-review-skills/find_oa_pdfs"
FIELDS = ["record_id", "doi", "title", "is_oa", "oa_status", "pdf_url",
          "landing_url", "source", "local_path", "note"]
MAX_PDF_BYTES = 100 * 1024 * 1024


class NotFound(Exception):
    """The API answered HTTP 404 for this DOI."""


class DownloadError(Exception):
    pass


def norm_doi(value: str) -> str:
    v = (value or "").strip()
    v = re.sub(r"^https?://(dx\.)?doi\.org/", "", v, flags=re.I)
    v = re.sub(r"^doi:\s*", "", v, flags=re.I)
    return v.strip().lower()


def http_json(url: str, timeout: int = 30) -> dict:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            raise NotFound(url) from exc
        raise


def openalex(doi: str, get: Callable[[str], dict]) -> dict:
    mail = os.environ.get("LRS_CONTACT_EMAIL", "")
    url = "https://api.openalex.org/works/doi:" + urllib.parse.quote(doi, safe="/")
    if mail:
        url += "?mailto=" + urllib.parse.quote(mail)
    data = get(url)
    oa = data.get("open_access") or {}
    best = data.get("best_oa_location") or {}
    pdf = best.get("pdf_url") or next(
        (loc.get("pdf_url") for loc in data.get("locations") or []
         if loc.get("is_oa") and loc.get("pdf_url")), "")
    return {"is_oa": bool(oa.get("is_oa")), "oa_status": oa.get("oa_status") or "",
            "pdf_url": pdf or "",
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
    lines = text.splitlines()
    first = lines[0] if lines else ""
    delim = "\t" if "\t" in first else ","
    header = [c.strip().strip('"').lower() for c in first.split(delim)]
    if "doi" not in header:  # plain DOI list: every non-empty line is data
        return [{"doi": line.strip()} for line in lines if line.strip()]
    rows = list(csv.DictReader(lines, delimiter=delim))
    return [{(k or "").strip().lower(): (v or "") for k, v in r.items()} for r in rows]


def safe_name(row: dict) -> str:
    """Readable stem plus a short hash of the DOI, so distinct DOIs never share a file."""
    base = re.sub(r"[^A-Za-z0-9._-]+", "_", row.get("record_id") or row["doi"])[:100]
    digest = hashlib.sha1(row["doi"].encode("utf-8")).hexdigest()[:8]
    return f"{base}-{digest}.pdf"


def download(url: str, dest: Path, timeout: int = 60, limit: int = MAX_PDF_BYTES) -> str:
    if urllib.parse.urlsplit(url).scheme.lower() not in ("http", "https"):
        raise DownloadError(f"refused non-http(s) URL: {url}")
    if dest.exists():
        return "exists, not overwritten"
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        final = resp.geturl() if hasattr(resp, "geturl") else url
        if urllib.parse.urlsplit(final).scheme.lower() not in ("http", "https"):
            raise DownloadError(f"redirected to non-http(s) URL: {final}")
        body = resp.read(limit + 1)
    if len(body) > limit:
        raise DownloadError(f"larger than {limit} bytes, not saved")
    if not body.startswith(b"%PDF"):
        raise DownloadError("link did not return a PDF; open landing_url in a browser")
    dest.write_bytes(body)
    return "saved"


def run(rows: list[dict], get=http_json, fetch=download, out_dir: Optional[Path] = None,
        pause: float = 0.2) -> tuple[list[dict], dict]:
    out = []
    stats = {"lookup_errors": 0, "not_checked": 0, "download_failed": 0}
    for row in rows:
        doi = norm_doi(row.get("doi", ""))
        rec = {k: "" for k in FIELDS}
        rec.update(record_id=row.get("record_id", ""), doi=doi, title=row.get("title", ""))
        if not doi:
            rec.update(oa_status="not_checked", note="no DOI; search the title in Google Scholar or ask the author")
            out.append(rec)
            continue
        hit, not_found, errored = None, 0, False
        for name, fn in (("openalex", openalex), ("unpaywall", unpaywall)):
            try:
                res = fn(doi, get)
            except NotFound:
                not_found += 1
                rec["note"] = (rec["note"] + f" {name}: DOI not found").strip()
                continue
            except Exception as exc:  # network, 5xx, JSON
                rec["note"] = (rec["note"] + f" {name} error: {exc}").strip()
                stats["lookup_errors"] += 1
                errored = True
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
        else:
            rec["oa_status"] = "not_found" if not_found and not errored else "not_checked"
            if rec["oa_status"] == "not_checked":
                stats["not_checked"] += 1
        if out_dir and rec["pdf_url"]:
            dest = out_dir / safe_name(rec)
            try:
                status = fetch(rec["pdf_url"], dest)
            except Exception as exc:
                status = f"download failed: {exc}"
                stats["download_failed"] += 1
            if status in ("saved", "exists, not overwritten"):
                rec["local_path"] = str(dest)
            rec["note"] = (rec["note"] + " " + status).strip()
        out.append(rec)
        time.sleep(pause)
    return out, stats


def main(argv: Optional[Sequence[str]] = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("input", help="TSV/CSV with a doi column, or a plain DOI list")
    ap.add_argument("-o", "--out", default="oa_check.csv")
    ap.add_argument("--force", action="store_true", help="overwrite an existing --out file")
    ap.add_argument("--download", metavar="DIR", help="save found OA PDFs here")
    args = ap.parse_args(argv)
    if Path(args.out).exists() and not args.force:
        print(f"ERROR {args.out} exists; pass --force to overwrite", file=sys.stderr)
        return 2
    try:
        rows = read_rows(Path(args.input))
    except (OSError, UnicodeDecodeError) as exc:
        print(f"ERROR {exc}", file=sys.stderr)
        return 2
    out_dir = Path(args.download) if args.download else None
    if out_dir:
        out_dir.mkdir(parents=True, exist_ok=True)
    result, stats = run(rows, out_dir=out_dir)
    with open(args.out, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(result)
    n_pdf = sum(1 for r in result if r["pdf_url"])
    n_closed = sum(1 for r in result if r["is_oa"] == "no")
    print(f"rows={len(result)} oa_pdf_found={n_pdf} closed={n_closed} "
          f"saved={sum(1 for r in result if r['local_path'])} "
          + " ".join(f"{k}={v}" for k, v in stats.items()) + f" -> {args.out}")
    return 1 if any(stats.values()) else 0


if __name__ == "__main__":
    sys.exit(main())
