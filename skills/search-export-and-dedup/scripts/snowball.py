#!/usr/bin/env python3
"""Backward and forward citation snowballing through OpenAlex.

For each seed DOI: backward = works the seed cites (referenced_works);
forward = works that cite the seed (filter=cites:). Candidates are
written as a CSV that dedup.py reads like any other export (title,
year, authors, journal, doi, pmid), plus seed_doi, direction and
openalex_id, and a JSON with counts for the PRISMA "other methods"
column. Nothing is screened here.

Polite use: sequential requests with a minimum gap, cursor paging with
per-page 200, OR-filters of at most 50 ids, a forward cap per seed
(--max-forward), one retry on 429/503, and a stop with a clear message
when the network is unreachable.

Environment variables (optional, never printed):
  OPENALEX_API_KEY   sent as api_key (OpenAlex requires a key for
                     production use; a few keyless calls work)
  LRS_CONTACT_EMAIL  sent as mailto and in the User-Agent
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Callable

API = "https://api.openalex.org/works"
TOOL = "literature-review-skills"
SELECT = "id,doi,title,publication_year,authorships,primary_location,ids"
OR_BATCH = 50
PER_PAGE = 200
OUT_COLUMNS = ["title", "year", "authors", "journal", "doi", "pmid",
               "openalex_id", "direction", "seed_doi"]


class NetworkUnavailable(Exception):
    pass


class OpenAlexError(Exception):
    partial = None


def normalize_doi(value) -> str:
    text = re.sub(r"^https?://(?:dx\.)?doi\.org/", "", str(value or "").strip(), flags=re.I)
    return re.sub(r"^doi:\s*", "", text, flags=re.I).rstrip(".").lower()


def short_id(value: str) -> str:
    return str(value or "").rstrip("/").rsplit("/", 1)[-1]


class Client:
    def __init__(self, opener: Callable | None = None, sleep=time.sleep,
                 clock=time.monotonic, gap: float = 0.15, timeout: float = 30.0):
        self._open = opener or urllib.request.urlopen
        self._sleep, self._clock, self.gap, self.timeout = sleep, clock, gap, timeout
        self._last = None
        self.contact = os.environ.get("LRS_CONTACT_EMAIL", "")
        self._key = os.environ.get("OPENALEX_API_KEY", "")
        self.calls = 0

    def get(self, path: str, params: dict) -> dict | None:
        params = dict(params)
        if self.contact:
            params["mailto"] = self.contact
        if self._key:
            params["api_key"] = self._key
        url = f"{API}{path}?{urllib.parse.urlencode(params, safe=':|,*/')}"
        ua = f"{TOOL}/snowball (https://github.com/Xuzhen-Li/literature-review-skills"
        ua += f"; mailto:{self.contact})" if self.contact else ")"
        for attempt in (1, 2):
            if self._last is not None:
                wait = self.gap - (self._clock() - self._last)
                if wait > 0:
                    self._sleep(wait)
            self._last = self._clock()
            self.calls += 1
            req = urllib.request.Request(url, headers={"User-Agent": ua, "Accept": "application/json"})
            try:
                with self._open(req, timeout=self.timeout) as resp:
                    return json.loads(resp.read().decode("utf-8"))
            except urllib.error.HTTPError as exc:
                if exc.code == 404:
                    return None
                if exc.code in (429, 503) and attempt == 1:
                    retry = exc.headers.get("Retry-After") if exc.headers else None
                    try:
                        self._sleep(min(float(retry), 60.0) if retry else 2.0)
                    except ValueError:
                        self._sleep(2.0)
                    continue
                raise OpenAlexError(f"OpenAlex HTTP {exc.code} for {path}") from None
            except (urllib.error.URLError, TimeoutError, OSError) as exc:
                raise NetworkUnavailable(str(getattr(exc, "reason", exc))) from None
        raise OpenAlexError("OpenAlex rate limit: retry later")


def to_row(work: dict, direction: str, seed: str) -> dict:
    loc = work.get("primary_location") or {}
    src = loc.get("source") or {}
    ids = work.get("ids") or {}
    authors = [((a.get("author") or {}).get("display_name") or "") for a in work.get("authorships") or []]
    return {
        "title": work.get("title") or "",
        "year": str(work.get("publication_year") or ""),
        "authors": "; ".join(a for a in authors if a),
        "journal": src.get("display_name") or "",
        "doi": normalize_doi(work.get("doi")),
        "pmid": short_id(ids.get("pmid", "")) if ids.get("pmid") else "",
        "openalex_id": short_id(work.get("id")),
        "direction": direction,
        "seed_doi": seed,
    }


def paged(client: Client, filt: str, limit: int | None = None):
    cursor, n = "*", 0
    while cursor:
        data = client.get("", {"filter": filt, "select": SELECT, "per-page": PER_PAGE, "cursor": cursor})
        if not data:
            return
        for w in data.get("results") or []:
            yield w
            n += 1
            if limit is not None and n >= limit:
                return
        cursor = (data.get("meta") or {}).get("next_cursor")


def snowball(seeds: list[str], client: Client, backward=True, forward=True, max_forward=500):
    rows, report = [], {"seeds": len(seeds), "seeds_not_found": [], "backward": 0, "forward": 0,
                        "forward_capped": []}
    try:
        _snowball_into(rows, report, seeds, client, backward, forward, max_forward)
    except OpenAlexError as exc:
        exc.partial = (rows, report)
        raise
    unique = {r["doi"] or r["openalex_id"] for r in rows}
    report["unique_candidates"] = len(unique - set(seeds))
    return rows, report


def _snowball_into(rows, report, seeds, client, backward, forward, max_forward):
    for seed in seeds:
        work = client.get(f"/doi:{urllib.parse.quote(seed, safe='/')}",
                          {"select": "id,doi,referenced_works,cited_by_count"})
        if not work:
            report["seeds_not_found"].append(seed)
            continue
        if backward:
            refs = [short_id(r) for r in work.get("referenced_works") or []]
            for i in range(0, len(refs), OR_BATCH):
                for w in paged(client, "openalex:" + "|".join(refs[i:i + OR_BATCH])):
                    rows.append(to_row(w, "backward", seed))
                    report["backward"] += 1
        if forward:
            if (work.get("cited_by_count") or 0) > max_forward:
                report["forward_capped"].append(seed)
            for w in paged(client, f"cites:{short_id(work.get('id'))}", limit=max_forward):
                rows.append(to_row(w, "forward", seed))
                report["forward"] += 1


def read_seeds(path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8-sig")
    if path.suffix.lower() in (".csv", ".tsv"):
        dialect = "excel-tab" if path.suffix.lower() == ".tsv" else "excel"
        with path.open(newline="", encoding="utf-8-sig") as fh:
            rows = list(csv.DictReader(fh, dialect=dialect))
        vals = [r.get("doi", "") for r in rows]
    else:
        vals = text.splitlines()
    seeds = []
    for v in vals:
        d = normalize_doi(v)
        if d and d not in seeds:
            seeds.append(d)
    return seeds


def main(argv=None, client: Client | None = None) -> int:
    ap = argparse.ArgumentParser(description="[[TODO-TEXT: one-line -h description of snowball.py]]")
    ap.add_argument("seeds", type=Path, help="[[TODO-TEXT: help for seeds file (included.tsv/CSV with doi column, or one DOI per line)]]")
    ap.add_argument("-o", "--out", type=Path, required=True, help="[[TODO-TEXT: help for --out candidates CSV]]")
    ap.add_argument("--report", type=Path, help="[[TODO-TEXT: help for --report counts JSON; default <out>.json]]")
    ap.add_argument("--direction", choices=["both", "backward", "forward"], default="both",
                    help="[[TODO-TEXT: help for --direction]]")
    ap.add_argument("--max-forward", type=int, default=500, help="[[TODO-TEXT: help for --max-forward cap per seed]]")
    args = ap.parse_args(argv)

    seeds = read_seeds(args.seeds)
    if not seeds:
        raise SystemExit("no seed DOIs found")
    client = client or Client()
    status = 0
    try:
        rows, report = snowball(seeds, client, backward=args.direction in ("both", "backward"),
                                forward=args.direction in ("both", "forward"), max_forward=args.max_forward)
    except NetworkUnavailable as exc:
        print(json.dumps({"error": "network unavailable", "detail": exc.args[0] if exc.args else ""}),
              file=sys.stderr)
        return 2
    except OpenAlexError as exc:
        rows, report = exc.partial
        report["incomplete"] = True
        report["error"] = str(exc)
        print(json.dumps({"error": str(exc), "incomplete": True}), file=sys.stderr)
        status = 1
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=OUT_COLUMNS)
        w.writeheader()
        w.writerows(rows)
    report["requests"] = client.calls
    rep = args.report or args.out.with_suffix(".json")
    rep.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"out": str(args.out), "report": str(rep), **report}))
    return status


if __name__ == "__main__":
    sys.exit(main())
