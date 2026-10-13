#!/usr/bin/env python3
"""Check that DOIs and PMIDs in a records table resolve and match.

Reads library.csv or evidence_table.csv. For each DOI it asks Crossref
(/works/{doi}); for each PMID it asks NCBI E-utilities esummary. The
remote title, year and first-author surname are compared with the row.
Nothing in the input is changed: results go to a separate CSV and every
row that is not "ok" is flagged [VERIFY].

Network use is opt-in per run (default on, --offline turns it off) and
polite: one request at a time with a minimum interval per host, a
User-Agent with a contact address, and a single retry on HTTP 429/503.

Environment variables (all optional, never printed):
  LRS_CONTACT_EMAIL  contact address for Crossref mailto / NCBI email
  NCBI_API_KEY       raises the NCBI limit from 3 to 10 requests/s
"""

from __future__ import annotations

import argparse
import csv
import difflib
import json
import os
import re
import sys
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Callable, Iterable

TOOL = "literature-review-skills"
CROSSREF_WORKS = "https://api.crossref.org/works/"
ESUMMARY = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"
ESUMMARY_BATCH = 200
TITLE_THRESHOLD = 0.90

OUT_COLUMNS = [
    "row_id",
    "id_type",
    "identifier",
    "status",
    "title_match",
    "year_match",
    "author_match",
    "remote_title",
    "remote_year",
    "remote_first_author",
    "flag",
    "detail",
]

STATUSES = ("ok", "mismatch", "not_found", "invalid", "unchecked", "error")

_DOI_FORMAT = re.compile(r"^10\.\d{4,9}/\S+$")
_PMID_FORMAT = re.compile(r"^[1-9]\d{0,8}$")
_YEAR = re.compile(r"\b(1[6-9]\d{2}|20\d{2})\b")


class NetworkUnavailable(Exception):
    """Raised when the remote service cannot be reached at all."""


# ---------------------------------------------------------------- normalizing

def normalize_doi(value) -> str:
    text = str(value or "").strip().lstrip("\ufeff")
    text = re.sub(r"^https?://(?:dx\.)?doi\.org/", "", text, flags=re.I)
    text = re.sub(r"^doi:\s*", "", text, flags=re.I)
    text = re.sub(r"\s*\[doi\]$", "", text, flags=re.I)
    return text.rstrip(".").strip().lower()


def normalize_pmid(value) -> str:
    text = str(value or "").strip()
    text = re.sub(r"^https?://pubmed\.ncbi\.nlm\.nih\.gov/", "", text, flags=re.I)
    text = re.sub(r"^pmid:?\s*", "", text, flags=re.I)
    text = text.strip("/ ")
    if text.endswith(".0") and text[:-2].isdigit():
        text = text[:-2]
    return text


def normalize_title(value) -> str:
    text = unicodedata.normalize("NFKD", str(value or ""))
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"[^\w\s]", " ", text.lower())
    return re.sub(r"\s+", " ", text).strip()


def surname_key(value) -> str:
    """Lowercase ASCII surname from 'Family, G.', 'Family G' or 'G. Family'."""
    text = str(value or "").strip()
    if not text:
        return ""
    text = text.split(";")[0].strip()
    if "," in text:
        text = text.split(",")[0]
    else:
        parts = text.split()
        # PubMed style "Kucsko G": trailing initials
        if len(parts) > 1 and re.fullmatch(r"[A-Z]{1,3}", parts[-1]):
            text = " ".join(parts[:-1])
        elif len(parts) > 1:
            text = parts[-1]
    return normalize_title(text).replace(" ", "")


def year_of(value) -> str:
    m = _YEAR.search(str(value or ""))
    return m.group(1) if m else ""


def titles_match(local: str, remote: str) -> bool:
    a, b = normalize_title(local), normalize_title(remote)
    if not a or not b:
        return False
    return a == b or difflib.SequenceMatcher(None, a, b).ratio() >= TITLE_THRESHOLD


# ---------------------------------------------------------------- http

class PoliteClient:
    """Sequential JSON GETs with per-host spacing and one 429/503 retry."""

    def __init__(self, opener: Callable | None = None, sleep=time.sleep,
                 clock=time.monotonic, contact: str | None = None,
                 timeout: float = 20.0):
        self._open = opener or urllib.request.urlopen
        self._sleep = sleep
        self._clock = clock
        self._last: dict[str, float] = {}
        self.contact = contact if contact is not None else os.environ.get("LRS_CONTACT_EMAIL", "")
        self.timeout = timeout
        self.intervals = {"api.crossref.org": 0.2, "eutils.ncbi.nlm.nih.gov": 0.34}

    def user_agent(self) -> str:
        ua = f"{TOOL}/verify_ids (https://github.com/Xuzhen-Li/literature-review-skills"
        if self.contact:
            ua += f"; mailto:{self.contact}"
        return ua + ")"

    def _wait(self, host: str) -> None:
        gap = self.intervals.get(host, 0.5)
        last = self._last.get(host)
        if last is not None:
            delay = gap - (self._clock() - last)
            if delay > 0:
                self._sleep(delay)
        self._last[host] = self._clock()

    def get_json(self, url: str):
        """Return (status_code, parsed_json_or_None)."""
        host = urllib.parse.urlsplit(url).hostname or ""
        for attempt in (1, 2):
            self._wait(host)
            req = urllib.request.Request(url, headers={
                "User-Agent": self.user_agent(),
                "Accept": "application/json",
            })
            try:
                with self._open(req, timeout=self.timeout) as resp:
                    return getattr(resp, "status", 200), json.loads(resp.read().decode("utf-8"))
            except urllib.error.HTTPError as exc:
                if exc.code in (429, 503) and attempt == 1:
                    retry = exc.headers.get("Retry-After") if exc.headers else None
                    try:
                        wait = min(float(retry), 60.0) if retry else 2.0
                    except ValueError:
                        wait = 2.0
                    self._sleep(wait)
                    continue
                return exc.code, None
            except (urllib.error.URLError, TimeoutError, OSError) as exc:
                raise NetworkUnavailable(str(getattr(exc, "reason", exc))) from None
            except ValueError:
                return 200, None
        return 429, None


# ---------------------------------------------------------------- lookups

def crossref_record(client: PoliteClient, doi: str):
    params = {}
    if client.contact:
        params["mailto"] = client.contact
    url = CROSSREF_WORKS + urllib.parse.quote(doi, safe="")
    if params:
        url += "?" + urllib.parse.urlencode(params)
    code, data = client.get_json(url)
    if code == 404:
        return "not_found", None
    if code != 200 or not isinstance(data, dict) or "message" not in data:
        return "error", f"crossref HTTP {code}"
    msg = data["message"]
    titles = msg.get("title") or [""]
    years = set()
    for key in ("issued", "published-print", "published-online", "published"):
        parts = (msg.get(key) or {}).get("date-parts") or [[None]]
        if parts and parts[0] and parts[0][0]:
            years.add(str(parts[0][0]))
    first = ""
    for author in msg.get("author") or []:
        if author.get("sequence") == "first" or not first:
            first = author.get("family") or author.get("name") or ""
            if author.get("sequence") == "first":
                break
    return "found", {"title": titles[0], "years": years, "first_author": first,
                     "doi": normalize_doi(msg.get("DOI"))}


def esummary_records(client: PoliteClient, pmids: list[str]) -> dict:
    """Map pmid -> record dict, or the string 'not_found' / 'error:<why>'."""
    out: dict = {}
    api_key = os.environ.get("NCBI_API_KEY", "")
    if api_key:
        client.intervals["eutils.ncbi.nlm.nih.gov"] = 0.1
    for start in range(0, len(pmids), ESUMMARY_BATCH):
        chunk = pmids[start:start + ESUMMARY_BATCH]
        params = {"db": "pubmed", "id": ",".join(chunk), "retmode": "json", "tool": TOOL}
        if client.contact:
            params["email"] = client.contact
        if api_key:
            params["api_key"] = api_key
        code, data = client.get_json(ESUMMARY + "?" + urllib.parse.urlencode(params))
        result = (data or {}).get("result") if isinstance(data, dict) else None
        if code != 200 or not isinstance(result, dict):
            for p in chunk:
                out[p] = f"error:esummary HTTP {code}"
            continue
        for p in chunk:
            rec = result.get(p)
            if not isinstance(rec, dict) or rec.get("error"):
                out[p] = "not_found"
                continue
            doi = ""
            for aid in rec.get("articleids") or []:
                if aid.get("idtype") == "doi":
                    doi = normalize_doi(aid.get("value"))
            out[p] = {
                "title": rec.get("title", ""),
                "years": {y for y in (year_of(rec.get("pubdate")), year_of(rec.get("epubdate"))) if y},
                "first_author": rec.get("sortfirstauthor", ""),
                "doi": doi,
            }
    return out


# ---------------------------------------------------------------- comparison

def _local_fields(row: dict) -> dict:
    first = row.get("first_author") or row.get("authors") or ""
    return {
        "title": row.get("title", ""),
        "year": year_of(row.get("year")),
        "first_author": first,
        "doi": normalize_doi(row.get("doi")),
    }


def compare(local: dict, remote: dict) -> dict:
    def tri(have_local, ok):
        if not have_local:
            return "n/a"
        return "yes" if ok else "no"

    title = tri(local["title"], titles_match(local["title"], remote["title"]))
    year = tri(local["year"], local["year"] in remote["years"])
    la, ra = surname_key(local["first_author"]), surname_key(remote["first_author"])
    author = tri(la and ra, la == ra)
    return {"title_match": title, "year_match": year, "author_match": author}


def _result(row_id, id_type, ident, status, detail="", matches=None, remote=None):
    rec = {c: "" for c in OUT_COLUMNS}
    rec.update(row_id=row_id, id_type=id_type, identifier=ident, status=status, detail=detail)
    if matches:
        rec.update(matches)
    if remote:
        rec["remote_title"] = remote["title"]
        rec["remote_year"] = ";".join(sorted(remote["years"]))
        rec["remote_first_author"] = remote["first_author"]
    rec["flag"] = "" if status == "ok" else "[VERIFY]"
    return rec


def _status_from(matches: dict) -> str:
    return "mismatch" if "no" in matches.values() else "ok"


def row_id_of(row: dict, index: int) -> str:
    for key in ("evidence_id", "record_id", "citation_key"):
        if row.get(key):
            return str(row[key]).strip()
    return f"row{index}"


def verify_rows(rows: Iterable[dict], client: PoliteClient | None, offline: bool = False):
    rows = list(rows)
    results: list[dict] = []
    online = not offline and client is not None
    pending_pmids: list[tuple[str, str, dict]] = []

    for i, row in enumerate(rows, start=2):
        rid = row_id_of(row, i)
        local = _local_fields(row)
        raw_doi, raw_pmid = row.get("doi", ""), row.get("pmid", "")
        doi, pmid = normalize_doi(raw_doi), normalize_pmid(raw_pmid)

        if str(raw_doi or "").strip():
            if not _DOI_FORMAT.match(doi):
                results.append(_result(rid, "doi", raw_doi, "invalid", "not a DOI (10.NNNN/suffix)"))
            elif not online:
                results.append(_result(rid, "doi", doi, "unchecked", "offline"))
            else:
                try:
                    state, rec = crossref_record(client, doi)
                except NetworkUnavailable as exc:
                    online = False
                    results.append(_result(rid, "doi", doi, "unchecked", f"network unavailable: {exc}"))
                else:
                    if state == "not_found":
                        results.append(_result(rid, "doi", doi, "not_found", "Crossref 404"))
                    elif state == "error":
                        results.append(_result(rid, "doi", doi, "error", rec))
                    else:
                        m = compare(local, rec)
                        results.append(_result(rid, "doi", doi, _status_from(m), "", m, rec))

        if str(raw_pmid or "").strip():
            if not _PMID_FORMAT.match(pmid):
                results.append(_result(rid, "pmid", raw_pmid, "invalid", "PMID must be digits"))
            else:
                pending_pmids.append((rid, pmid, local))

    if pending_pmids:
        lookup: dict = {}
        if online:
            try:
                lookup = esummary_records(client, sorted({p for _, p, _ in pending_pmids}))
            except NetworkUnavailable as exc:
                online = False
                lookup = {p: f"unchecked:network unavailable: {exc}" for _, p, _ in pending_pmids}
        for rid, pmid, local in pending_pmids:
            rec = lookup.get(pmid) if lookup else None
            if rec is None:
                results.append(_result(rid, "pmid", pmid, "unchecked", "offline"))
            elif rec == "not_found":
                results.append(_result(rid, "pmid", pmid, "not_found", "esummary: no document"))
            elif isinstance(rec, str):
                state, _, why = rec.partition(":")
                results.append(_result(rid, "pmid", pmid, state, why))
            else:
                m = compare(local, rec)
                detail = ""
                status = _status_from(m)
                if local["doi"] and rec["doi"] and local["doi"] != rec["doi"]:
                    status, detail = "mismatch", f"PubMed lists DOI {rec['doi']}"
                results.append(_result(rid, "pmid", pmid, status, detail, m, rec))

    order = {id(r): n for n, r in enumerate(results)}
    results.sort(key=lambda r: (r["row_id"], r["id_type"], order[id(r)]))
    return results


# ---------------------------------------------------------------- cli

def read_rows(path: Path) -> list[dict]:
    with path.open(newline="", encoding="utf-8-sig") as fh:
        reader = csv.DictReader(fh)
        missing = {"doi", "pmid"} - {(h or "").strip().lower() for h in reader.fieldnames or []}
        if missing == {"doi", "pmid"}:
            raise SystemExit(f"{path}: needs a doi or pmid column")
        return [{(k or "").strip().lower(): (v or "") for k, v in r.items()} for r in reader]


def write_results(path: Path, results: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=OUT_COLUMNS)
        w.writeheader()
        w.writerows(results)


def summarize(results: list[dict]) -> dict:
    counts = {s: 0 for s in STATUSES}
    for r in results:
        counts[r["status"]] += 1
    return counts


def main(argv=None, client: PoliteClient | None = None) -> int:
    ap = argparse.ArgumentParser(description="[[TODO-TEXT: one-line -h description of verify_ids.py]]")
    ap.add_argument("table", type=Path, help="[[TODO-TEXT: help for input table]]")
    ap.add_argument("-o", "--out", type=Path, default=None,
                    help="[[TODO-TEXT: help for --out; default evidence/identifier_check.csv next to input]]")
    ap.add_argument("--offline", action="store_true", help="[[TODO-TEXT: help for --offline]]")
    ap.add_argument("--strict", action="store_true", help="[[TODO-TEXT: help for --strict exit code]]")
    args = ap.parse_args(argv)

    rows = read_rows(args.table)
    if client is None and not args.offline:
        client = PoliteClient()
    results = verify_rows(rows, client, offline=args.offline)
    out = args.out or args.table.parent / "identifier_check.csv"
    write_results(out, results)
    counts = summarize(results)
    print(json.dumps({"out": str(out), **counts}))
    bad = counts["mismatch"] + counts["not_found"] + counts["invalid"]
    return 1 if args.strict and bad else 0


if __name__ == "__main__":
    sys.exit(main())
