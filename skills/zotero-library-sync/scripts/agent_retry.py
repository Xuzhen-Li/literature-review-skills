#!/usr/bin/env python3
"""Agent retry: the step between find_oa_pdfs.py and please_fetch.py.

Many open-access links refuse a script (HTTP 403, an HTML landing page, 429)
but open fine in the agent's own browser or web-fetch tool. Before anything
goes to the human, the agent retries every such paper itself.

  worklist  read oa_check.csv, write agent_retry.tsv: one row per paper with no
            local_path and a DOI, with the landing URL, every candidate OA URL
            (the failed pdf_url, doi.org, OpenAlex locations with
            --openalex-locations, Europe PMC / PMC copies, preprint servers,
            known publisher PDF URL patterns) and the save_as path. The agent
            opens the candidates with its own tools, saves a real PDF under
            save_as, or fills agent_retry=failed and a reason.
  accept    ingest what the agent saved: a file counts only if it starts with
            %PDF-; it is copied into the PDF folder without overwriting, and
            the merged status (oa_check columns + agent_retry, agent_reason)
            is written to -o. Feed that file to please_fetch.py --status.

Only legal OA copies. Shadow libraries (BLOCKED_HOST_PARTS) are never listed.
The agent never types a password, captcha, or second factor.
Exit codes: 0 ok; 1 (accept) some worklist rows were neither saved nor marked
failed, so the agent has not finished; 2 bad input or existing output without
--force.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import shutil
import sys
import urllib.parse
from pathlib import Path
from typing import Callable, Optional, Sequence

sys.path.insert(0, str(Path(__file__).resolve().parent))
import find_oa_pdfs as foa  # noqa: E402
import please_fetch as pf  # noqa: E402

WORK_FIELDS = ["record_id", "doi", "title", "landing_url", "candidate_urls", "save_as",
               "agent_retry", "agent_reason"]
RETRY_VALUES = ("got", "failed")


def publisher_patterns(doi: str) -> list[str]:
    """Known direct-PDF URL shapes for OA publishers and preprint servers."""
    d = doi.lower()
    pre, _, suf = d.partition("/")
    q = urllib.parse.quote(doi, safe="/()")
    out = []
    if pre == "10.3390":
        out.append(f"https://www.mdpi.com/{q}/pdf")  # resolves via doi path on mdpi
    if pre in ("10.1111", "10.1002"):
        out.append(f"https://onlinelibrary.wiley.com/doi/pdfdirect/{q}")
    if pre == "10.1073":
        out.append(f"https://www.pnas.org/doi/pdf/{q}")
    if pre == "10.1128":
        out.append(f"https://journals.asm.org/doi/pdf/{q}")
    if pre == "10.3389":
        out.append(f"https://www.frontiersin.org/articles/{q}/pdf")
    if pre == "10.1038":
        out.append(f"https://www.nature.com/articles/{suf}.pdf")
    if pre == "10.1186":
        out.append(f"https://link.springer.com/content/pdf/{q}.pdf")
    if pre == "10.1101":
        out.append(f"https://www.biorxiv.org/content/{q}.full.pdf")
        out.append(f"https://www.medrxiv.org/content/{q}.full.pdf")
    if pre == "10.48550":
        out.append(f"https://arxiv.org/pdf/{suf.split('arxiv.', 1)[-1]}")
    return out


def europepmc_candidates(doi: str) -> list[str]:
    q = urllib.parse.quote(f'DOI:"{doi}"')
    return [f"https://europepmc.org/search?query={q}"]


def openalex_locations(doi: str, get: Callable[[str], dict]) -> list[str]:
    """Every OA location OpenAlex knows (repositories, preprints), PDF first."""
    data = get("https://api.openalex.org/works/doi:" + urllib.parse.quote(doi, safe="/"))
    urls = []
    for loc in data.get("locations") or []:
        if loc.get("is_oa"):
            urls += [loc.get("pdf_url") or "", loc.get("landing_page_url") or ""]
    return [u for u in urls if u]


def candidates(row: dict, extra: Sequence[str] = ()) -> list[str]:
    doi = foa.norm_doi(row.get("doi", ""))
    raw = [row.get("pdf_url", ""), *extra, *publisher_patterns(doi), row.get("landing_url", ""),
           f"https://doi.org/{doi}", *europepmc_candidates(doi)]
    seen, out = set(), []
    for u in raw:
        if u and u not in seen and urllib.parse.urlsplit(u).scheme in ("http", "https") \
                and not foa.blocked_host(u):
            seen.add(u)
            out.append(u)
    return out


def worklist(status: list[dict], incoming: str, get=None) -> list[dict]:
    rows = []
    for r in status:
        doi = foa.norm_doi(r.get("doi", ""))
        if r.get("local_path") or not doi:
            continue
        extra: list[str] = []
        if get is not None:
            try:
                extra = openalex_locations(doi, get)
            except Exception:
                extra = []
        stem = pf.upload_stem(r.get("record_id", ""), doi)
        rows.append({"record_id": r.get("record_id", ""), "doi": doi, "title": r.get("title", ""),
                     "landing_url": r.get("landing_url", "") or f"https://doi.org/{doi}",
                     "candidate_urls": " | ".join(candidates(r, extra)),
                     "save_as": f"{incoming.rstrip('/')}/{stem}.pdf",
                     "agent_retry": "", "agent_reason": ""})
    return rows


def accept(status: list[dict], work: list[dict], incoming: Path, pdf_dir: Path):
    """Return (merged_status_rows, unfinished_keys)."""
    by_key = {}
    for w in work:
        by_key[w.get("record_id") or foa.norm_doi(w.get("doi", ""))] = w
    merged, unfinished = [], []
    pdf_dir.mkdir(parents=True, exist_ok=True)
    for r in status:
        r = dict(r)
        r.setdefault("agent_retry", "")
        r.setdefault("agent_reason", "")
        w = by_key.get(r.get("record_id") or foa.norm_doi(r.get("doi", "")))
        if w is None or r.get("local_path"):
            merged.append(r)
            continue
        src = incoming / Path(w["save_as"]).name
        said = (w.get("agent_retry") or "").strip().lower()
        if said and said not in RETRY_VALUES:
            raise ValueError(f"agent_retry must be got or failed: {w.get('record_id') or w['doi']}")
        if src.exists() and pf._is_pdf(src):
            dest = pdf_dir / src.name
            if not dest.exists():
                shutil.copyfile(src, dest)
            elif not pf._is_pdf(dest) or hashlib.sha1(dest.read_bytes()).digest() != \
                    hashlib.sha1(src.read_bytes()).digest():
                dest = pdf_dir / f"{src.stem}-agent.pdf"
                if dest.exists():
                    raise ValueError(f"{dest} exists; not overwriting")
                shutil.copyfile(src, dest)
            r.update(local_path=str(dest), agent_retry="got",
                     agent_reason=w.get("agent_reason") or "saved by agent")
        elif src.exists():
            r.update(agent_retry="failed", agent_reason="saved file is not a PDF (no %PDF- header)")
        elif said == "failed":
            if not (w.get("agent_reason") or "").strip():
                raise ValueError(f"agent_retry=failed needs a reason: {w.get('record_id') or w['doi']}")
            r.update(agent_retry="failed", agent_reason=w["agent_reason"].strip())
        else:
            if said == "got":
                r.update(agent_retry="failed", agent_reason=f"marked got but no file at {w['save_as']}")
            else:
                unfinished.append(w.get("record_id") or w["doi"])
        merged.append(r)
    return merged, unfinished


def _write(path: Path, fields, rows, delim):
    with path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=fields, delimiter=delim, extrasaction="ignore", lineterminator="\n")
        w.writeheader()
        w.writerows(rows)


def main(argv: Optional[Sequence[str]] = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("worklist")
    a.add_argument("status", type=Path, help="oa_check.csv from find_oa_pdfs.py")
    a.add_argument("-o", "--out", type=Path, default=Path("04-library/agent_retry.tsv"))
    a.add_argument("--incoming", default="04-library/agent_pdfs", help="where the agent saves PDFs")
    a.add_argument("--openalex-locations", action="store_true",
                   help="also ask OpenAlex for every OA location (repositories, preprints)")
    a.add_argument("--force", action="store_true")
    b = sub.add_parser("accept")
    b.add_argument("--status", type=Path, required=True)
    b.add_argument("--worklist", type=Path, required=True)
    b.add_argument("--incoming", type=Path, required=True)
    b.add_argument("--pdf-dir", type=Path, required=True, help="04-library/pdfs")
    b.add_argument("-o", "--out", type=Path, required=True)
    b.add_argument("--force", action="store_true")
    args = ap.parse_args(argv)
    if args.out.exists() and not args.force:
        print(f"ERROR {args.out} exists; pass --force to overwrite", file=sys.stderr)
        return 2
    try:
        status = pf._read(args.status)
        if args.cmd == "worklist":
            rows = worklist(status, args.incoming, foa.http_json if args.openalex_locations else None)
            args.out.parent.mkdir(parents=True, exist_ok=True)
            _write(args.out, WORK_FIELDS, rows, "\t")
            print(f"OK agent_retry rows={len(rows)} -> {args.out}")
            return 0
        merged, unfinished = accept(status, pf._read(args.worklist), args.incoming, args.pdf_dir)
    except (OSError, ValueError) as exc:
        print(f"ERROR {exc}", file=sys.stderr)
        return 2
    fields = list(foa.FIELDS) + [k for k in ("agent_retry", "agent_reason") if k not in foa.FIELDS]
    fields += [k for k in (merged[0] if merged else {}) if k not in fields]
    _write(args.out, fields, merged, ",")
    got = sum(1 for r in merged if r.get("agent_retry") == "got")
    failed = sum(1 for r in merged if r.get("agent_retry") == "failed")
    print(f"OK got={got} failed={failed} unfinished={len(unfinished)} -> {args.out}")
    if unfinished:
        print("NOT DONE agent has not tried: " + ", ".join(unfinished), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
