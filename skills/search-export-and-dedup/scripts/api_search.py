#!/usr/bin/env python3
"""Run the locked search against free scholarly APIs and save one CSV per source.

No account, login, or API key is needed. Sources (default: openalex, europepmc,
pubmed, semanticscholar, arxiv; crossref on request):

  openalex         https://api.openalex.org/works?search=      (keyless: first 10,000 hits)
  europepmc        Europe PMC REST search; includes PubMed records and bioRxiv/medRxiv
                   preprints (SRC:PPR)
  pubmed           NCBI E-utilities esearch + efetch (abstracts included)
  semanticscholar  /graph/v1/paper/search/bulk
  arxiv            export.arxiv.org Atom API
  crossref         /works?query= (relevance-ranked and noisy; off by default)

Each source writes <out-dir>/<source>_<YYYYMMDD>.csv with the columns dedup.py reads
(title, year, authors, journal, doi, pmid, abstract) plus pdf_url and source_id.
With --hit-counts it appends one row per source to 01-search/hit_counts.tsv
(database,interface,date,count,notes): count is the total the API reported, and
notes say how many records were retrieved. --count-only prints totals and writes
no record files (feasibility counts for scoping).

Optional environment variables (never printed): LRS_CONTACT_EMAIL (polite mailto),
OPENALEX_API_KEY, NCBI_API_KEY, S2_API_KEY.
Exit 0 when every source succeeded; 1 when a source failed or was truncated by
--max (other sources still written); 2 on bad arguments or an existing output file.
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
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

try:
    from defusedxml.ElementTree import fromstring as xml_fromstring
except ImportError:  # API responses carry no DOCTYPE; refuse one if present
    import xml.etree.ElementTree as _ET

    def xml_fromstring(data):
        if isinstance(data, str):
            data = data.encode("utf-8")
        if b"<!DOCTYPE" in data[:4096] or b"<!ENTITY" in data:
            raise ValueError("XML declares a DOCTYPE/ENTITY; refusing to parse")
        return _ET.fromstring(data)

UA = "literature-review-skills/api_search"
FIELDS = ["title", "year", "authors", "journal", "doi", "pmid", "abstract", "pdf_url", "source_id"]
DEFAULT_SOURCES = ["openalex", "europepmc", "pubmed", "semanticscholar", "arxiv"]
ALL_SOURCES = DEFAULT_SOURCES + ["crossref"]
INTERFACE = {
    "openalex": "OpenAlex API",
    "europepmc": "Europe PMC REST API",
    "pubmed": "NCBI E-utilities",
    "semanticscholar": "Semantic Scholar Graph API",
    "arxiv": "arXiv API",
    "crossref": "Crossref REST API",
}


SLEEP = time.sleep  # tests replace this


class SourceError(Exception):
    pass


def http_get(url: str, headers: Optional[dict] = None, timeout: int = 60,
             sleep: Callable[[float], None] = time.sleep) -> bytes:
    """GET with one retry on 429/503. Raises SourceError on failure."""
    h = {"User-Agent": UA}
    h.update(headers or {})
    for attempt in (1, 2):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=h), timeout=timeout) as r:
                return r.read()
        except urllib.error.HTTPError as exc:
            if exc.code in (429, 503) and attempt == 1:
                sleep(5)
                continue
            msg = f"HTTP {exc.code} from {urllib.parse.urlsplit(url).netloc}"
            try:
                body = json.loads(exc.read().decode("utf-8", "replace"))
                detail = body.get("errMsg") or body.get("message") or body.get("error")
                if isinstance(detail, str) and detail:
                    msg += f" ({detail[:150]})"
            except Exception:
                pass
            raise SourceError(msg) from exc
        except (urllib.error.URLError, OSError) as exc:
            raise SourceError(f"network error: {exc}") from exc
    raise SourceError("unreachable")


def _json(get, url, headers=None):
    try:
        return json.loads(get(url, headers).decode("utf-8"))
    except (ValueError, UnicodeDecodeError) as exc:
        raise SourceError(f"bad JSON from {urllib.parse.urlsplit(url).netloc}") from exc


def norm_doi(v) -> str:
    v = (v or "").strip()
    v = re.sub(r"^https?://(dx\.)?doi\.org/", "", v, flags=re.I)
    return re.sub(r"^doi:\s*", "", v, flags=re.I).lower()


def _clean(text) -> str:
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", text or "")).strip()


def _rec(**kw) -> dict:
    r = {k: "" for k in FIELDS}
    r.update({k: ("" if v is None else str(v)) for k, v in kw.items()})
    r["doi"] = norm_doi(r["doi"])
    r["title"], r["abstract"] = _clean(r["title"]), _clean(r["abstract"])
    return r


def _q(params: dict) -> str:
    return urllib.parse.urlencode({k: v for k, v in params.items() if v not in (None, "")})


# ---- sources: each returns (total_reported, records) ----

def src_openalex(query, max_n, get, count_only=False):
    key, mail = os.environ.get("OPENALEX_API_KEY", ""), os.environ.get("LRS_CONTACT_EMAIL", "")
    out, page, total = [], 1, 0
    while True:
        url = "https://api.openalex.org/works?" + _q({
            "search": query, "per_page": 1 if count_only else 100, "page": page,
            "api_key": key, "mailto": mail})
        data = _json(get, url)
        total = int((data.get("meta") or {}).get("count") or 0)
        if count_only:
            return total, []
        res = data.get("results") or []
        for w in res:
            inv = w.get("abstract_inverted_index") or {}
            words = sorted(((i, t) for t, idx in inv.items() for i in idx))
            loc = w.get("primary_location") or {}
            best = w.get("best_oa_location") or {}
            out.append(_rec(
                title=w.get("title"), year=w.get("publication_year"),
                authors="; ".join((a.get("author") or {}).get("display_name", "") for a in w.get("authorships") or []),
                journal=(loc.get("source") or {}).get("display_name"), doi=w.get("doi"),
                pmid=((w.get("ids") or {}).get("pmid") or "").rsplit("/", 1)[-1],
                abstract=" ".join(t for _, t in words), pdf_url=best.get("pdf_url"),
                source_id=w.get("id")))
        if not res or len(out) >= min(max_n, total) or page * 100 >= 10000:
            return total, out[:max_n]
        page += 1


def src_europepmc(query, max_n, get, count_only=False):
    out, cursor, total = [], "*", 0
    while True:
        url = "https://www.ebi.ac.uk/europepmc/webservices/rest/search?" + _q({
            "query": query, "format": "json", "resultType": "core",
            "pageSize": 1 if count_only else max(1, min(1000, max_n)), "cursorMark": cursor})
        data = _json(get, url)
        total = int(data.get("hitCount") or 0)
        if count_only:
            return total, []
        res = (data.get("resultList") or {}).get("result") or []
        for r in res:
            pdf = ""
            for u in ((r.get("fullTextUrlList") or {}).get("fullTextUrl") or []):
                if u.get("documentStyle") == "pdf" and u.get("availabilityCode") in ("OA", "F"):
                    pdf = u.get("url", "")
                    break
            out.append(_rec(
                title=r.get("title"), year=r.get("pubYear"), authors=(r.get("authorString") or "").replace(", ", "; "),
                journal=((r.get("journalInfo") or {}).get("journal") or {}).get("title") or ("preprint" if r.get("source") == "PPR" else ""),
                doi=r.get("doi"), pmid=r.get("pmid"), abstract=r.get("abstractText"),
                pdf_url=pdf, source_id=f"{r.get('source', '')}:{r.get('id', '')}"))
        nxt = data.get("nextCursorMark")
        if not res or not nxt or nxt == cursor or len(out) >= min(max_n, total):
            return total, out[:max_n]
        cursor = nxt


def src_pubmed(query, max_n, get, count_only=False):
    base = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"
    extra = {"api_key": os.environ.get("NCBI_API_KEY", ""), "email": os.environ.get("LRS_CONTACT_EMAIL", ""),
             "tool": "literature-review-skills"}
    data = _json(get, base + "esearch.fcgi?" + _q({"db": "pubmed", "term": query, "retmode": "json",
                                                   "retmax": 0 if count_only else min(max_n, 9999), **extra}))
    es = data.get("esearchresult") or {}
    total = int(es.get("count") or 0)
    ids = es.get("idlist") or []
    out = []
    if count_only:
        return total, []
    for i in range(0, len(ids), 200):
        root = xml_fromstring(get(base + "efetch.fcgi?" + _q({"db": "pubmed", "id": ",".join(ids[i:i + 200]),
                                                               "retmode": "xml", **extra}), None))
        for art in root.iter("PubmedArticle"):
            mc = art.find("MedlineCitation")
            a = mc.find("Article") if mc is not None else None
            if a is None:
                continue
            doi = next((e.text for e in art.iter("ArticleId") if e.get("IdType") == "doi"), "")
            year = a.findtext("Journal/JournalIssue/PubDate/Year") or (a.findtext("Journal/JournalIssue/PubDate/MedlineDate") or "")[:4]
            authors = "; ".join(f"{au.findtext('LastName', '')} {au.findtext('Initials', '')}".strip()
                                for au in a.iter("Author") if au.findtext("LastName"))
            out.append(_rec(
                title="".join(a.find("ArticleTitle").itertext()) if a.find("ArticleTitle") is not None else "",
                year=year, authors=authors, journal=a.findtext("Journal/Title"), doi=doi,
                pmid=mc.findtext("PMID"),
                abstract=" ".join("".join(t.itertext()) for t in a.iter("AbstractText")),
                source_id="PMID:" + (mc.findtext("PMID") or "")))
    return total, out


def src_semanticscholar(query, max_n, get, count_only=False):
    key = os.environ.get("S2_API_KEY", "")
    headers = {"x-api-key": key} if key else None
    out, token, total = [], None, 0
    while True:
        url = "https://api.semanticscholar.org/graph/v1/paper/search/bulk?" + _q({
            "query": query, "token": token,
            "fields": "title,year,authors,venue,externalIds,abstract,openAccessPdf"})
        data = _json(get, url, headers)
        total = int(data.get("total") or 0)
        if count_only:
            return total, []
        res = data.get("data") or []
        for p in res:
            ext = p.get("externalIds") or {}
            out.append(_rec(
                title=p.get("title"), year=p.get("year"),
                authors="; ".join(a.get("name", "") for a in p.get("authors") or []),
                journal=p.get("venue"), doi=ext.get("DOI"), pmid=ext.get("PubMed"),
                abstract=p.get("abstract"), pdf_url=(p.get("openAccessPdf") or {}).get("url"),
                source_id="S2:" + str(p.get("paperId", ""))))
        token = data.get("token")
        if not res or not token or len(out) >= min(max_n, total):
            return total, out[:max_n]


ATOM = "{http://www.w3.org/2005/Atom}"
OS_NS = "{http://a9.com/-/spec/opensearch/1.1/}"
ARXIV_NS = "{http://arxiv.org/schemas/atom}"


def arxiv_query(query: str) -> str:
    """arXiv ORs bare words ('all:a b' matches a OR b), so AND plain terms."""
    q = query.strip()
    if ":" in q or re.search(r"\b(AND|OR|ANDNOT)\b", q):
        return q
    terms = re.findall(r'"[^"]+"|\S+', q)
    return " AND ".join(f"all:{t}" for t in terms)


def src_arxiv(query, max_n, get, count_only=False):
    out, start, total = [], 0, 0
    while True:
        url = "https://export.arxiv.org/api/query?" + _q({
            "search_query": arxiv_query(query), "start": start,
            "max_results": 1 if count_only else min(500, max_n)})
        root = xml_fromstring(get(url, None))
        total = int(root.findtext(OS_NS + "totalResults") or 0)
        if count_only:
            return total, []
        entries = root.findall(ATOM + "entry")
        for e in entries:
            aid = (e.findtext(ATOM + "id") or "").rsplit("/abs/", 1)[-1]
            pdf = next((l.get("href") for l in e.findall(ATOM + "link") if l.get("title") == "pdf"), "")
            out.append(_rec(
                title=e.findtext(ATOM + "title"), year=(e.findtext(ATOM + "published") or "")[:4],
                authors="; ".join(a.findtext(ATOM + "name", "") for a in e.findall(ATOM + "author")),
                journal=e.findtext(ARXIV_NS + "journal_ref") or "arXiv",
                doi=e.findtext(ARXIV_NS + "doi") or (f"10.48550/arxiv.{re.sub(r'v[0-9]+$', '', aid)}" if aid else ""),
                abstract=e.findtext(ATOM + "summary"), pdf_url=pdf, source_id="arXiv:" + aid))
        start += len(entries)
        if not entries or len(out) >= min(max_n, total):
            return total, out[:max_n]
        SLEEP(3)  # arXiv asks for 3 s between calls


def src_crossref(query, max_n, get, count_only=False):
    mail = os.environ.get("LRS_CONTACT_EMAIL", "")
    out, cursor, total = [], "*", 0
    while True:
        url = "https://api.crossref.org/works?" + _q({"query": query, "rows": 0 if count_only else 1000,
                                                      "cursor": cursor, "mailto": mail})
        msg = _json(get, url).get("message") or {}
        total = int(msg.get("total-results") or 0)
        if count_only:
            return total, []
        items = msg.get("items") or []
        for it in items:
            parts = ((it.get("issued") or {}).get("date-parts") or [[None]])[0]
            out.append(_rec(
                title=(it.get("title") or [""])[0], year=parts[0] if parts else "",
                authors="; ".join(f"{a.get('family', '')} {a.get('given', '')}".strip() for a in it.get("author") or []),
                journal=(it.get("container-title") or [""])[0], doi=it.get("DOI"),
                abstract=it.get("abstract"), source_id="crossref"))
        nxt = msg.get("next-cursor")
        if not items or not nxt or len(out) >= min(max_n, total):
            return total, out[:max_n]
        cursor = nxt


SOURCES = {"openalex": src_openalex, "europepmc": src_europepmc, "pubmed": src_pubmed,
           "semanticscholar": src_semanticscholar, "arxiv": src_arxiv, "crossref": src_crossref}


def run(queries: dict, max_n: int, get, count_only: bool = False, pause: float = 0.4):
    """queries: source -> query string. Returns {source: {total, records, error}}."""
    results = {}
    for name, query in queries.items():
        try:
            total, recs = SOURCES[name](query, max_n, get, count_only)
            results[name] = {"total": total, "records": recs, "error": ""}
        except (SourceError, ValueError, KeyError, AttributeError) as exc:
            results[name] = {"total": None, "records": [], "error": str(exc)}
        SLEEP(pause)
    return results


def main(argv: Optional[Sequence[str]] = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--query", help="query used for every source without its own --<source>-query")
    for s in ALL_SOURCES:
        ap.add_argument(f"--{s}-query", dest=f"q_{s}", help=f"query in {s} syntax")
    ap.add_argument("--sources", default=",".join(DEFAULT_SOURCES),
                    help=f"comma list from {','.join(ALL_SOURCES)} (default: %(default)s)")
    ap.add_argument("--max", type=int, default=2000, help="records per source (default 2000)")
    ap.add_argument("--out-dir", help="02-records/raw; required unless --count-only")
    ap.add_argument("--hit-counts", help="append rows to this hit_counts.tsv")
    ap.add_argument("--count-only", action="store_true")
    ap.add_argument("--date", default=dt.date.today().strftime("%Y%m%d"), help=argparse.SUPPRESS)
    args = ap.parse_args(argv)
    names = [s.strip() for s in args.sources.split(",") if s.strip()]
    bad = [s for s in names if s not in SOURCES]
    if bad:
        print(f"ERROR unknown source(s): {', '.join(bad)}", file=sys.stderr)
        return 2
    queries = {s: getattr(args, f"q_{s}") or args.query for s in names}
    missing = [s for s, q in queries.items() if not q]
    if missing:
        print(f"ERROR no query for: {', '.join(missing)}", file=sys.stderr)
        return 2
    out_dir = Path(args.out_dir) if args.out_dir else None
    if not args.count_only:
        if not out_dir:
            print("ERROR --out-dir is required unless --count-only", file=sys.stderr)
            return 2
        clash = [str(out_dir / f"{s}_{args.date}.csv") for s in names if (out_dir / f"{s}_{args.date}.csv").exists()]
        if clash:
            print(f"ERROR exists, not overwritten: {', '.join(clash)}", file=sys.stderr)
            return 2
        out_dir.mkdir(parents=True, exist_ok=True)
    results = run(queries, args.max, lambda u, h=None: http_get(u, h))
    iso = f"{args.date[:4]}-{args.date[4:6]}-{args.date[6:]}"
    rows, failed = [], False
    for s in names:
        r = results[s]
        if r["error"]:
            failed = True
            print(f"{s}: FAILED {r['error']}")
            rows.append([s, INTERFACE[s], iso, "[VERIFY]", f"api_search failed: {r['error']}; query: {queries[s]}"])
            continue
        n = len(r["records"])
        note = f"api_search; query: {queries[s]}"
        if not args.count_only:
            path = out_dir / f"{s}_{args.date}.csv"
            with open(path, "w", newline="", encoding="utf-8") as fh:
                w = csv.DictWriter(fh, fieldnames=FIELDS)
                w.writeheader()
                w.writerows(r["records"])
            note = f"api_search retrieved {n} of {r['total']}; file {path.name}; query: {queries[s]}"
            if n < r["total"]:
                failed = True
                note += "; TRUNCATED by --max or API paging limit"
        print(f"{s}: total={r['total']}" + ("" if args.count_only else f" saved={n}"))
        rows.append([s, INTERFACE[s], iso, str(r["total"]), note])
    if args.hit_counts:
        hc = Path(args.hit_counts)
        new = not hc.exists() or hc.stat().st_size == 0
        with open(hc, "a", newline="", encoding="utf-8") as fh:
            delim = "\t"
            if not new:  # keep whatever delimiter the existing header uses
                with open(hc, encoding="utf-8") as rh:
                    first = rh.readline()
                if "\t" not in first and "," in first:
                    delim = ","
            w = csv.writer(fh, delimiter=delim)
            if new:
                w.writerow(["database", "interface", "date", "count", "notes"])
            w.writerows(rows)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
