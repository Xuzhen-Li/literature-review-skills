---
name: search-export-and-dedup
description: >
  Runs the locked searches through free APIs itself (scripts/api_search.py),
  adds any optional manual RIS/NBIB/CSV exports, runs scripts/dedup.py, and
  writes library.csv plus PRISMA identification counts. Trigger on "export the search", "deduplicate", "merge the RIS
  files", or "PRISMA counts". Do not use it before the search lock, and
  do not use it to screen for eligibility.
---

# Search export and deduplication

## Opening

On first use in a project, say this verbatim:

I am search export and deduplication. I download search results from free databases myself, merge them, and never drop records just to make the hit counts match. You do not need to export anything.

## When to use

`gates.search_lock` is true and `01-search/search_strings.md` holds the locked strings. This skill identifies records. Eligibility decisions belong to `literature-screening`.

## Inputs (paths) / Preconditions

- Locked strings and `01-search/hit_counts.tsv`.
- A place to put exports: `<project>/02-records/raw/`.
- `scripts/dedup.py` in this skill directory (follow the symlink to the real path). Tests live in `tests/test_dedup.py`.
- `scripts/verify_ids.py`, tests in `tests/test_verify_ids.py`. Reads `library.csv` or `evidence_table.csv` (a CSV table with `doi` or `pmid` columns). Optional environment variables: `LRS_CONTACT_EMAIL` (polite contact email for Crossref and NCBI queries) and `NCBI_API_KEY` (NCBI key enabling faster request rates); both are optional and never printed.
- `scripts/api_search.py`, tests in `tests/test_api_search.py`. No login or key is needed. Optional keys: `OPENALEX_API_KEY`, `NCBI_API_KEY`, `S2_API_KEY`, and `LRS_CONTACT_EMAIL`; never printed.
- Optional subscription databases only (`use_subscription_databases: true`): the user performs logins. Do not type a password or complete a publisher login. Open the database in the agent browser; if it is not logged in, use computer control of the user's desktop browser when available and let the user sign in. Do not ask for, type, or store a password, captcha, or second factor. Do not switch to an unauthorized copy.

## Procedure (numbered steps)

1. Create `<project>/02-records/raw/` if it is missing.
2. Default: run the locked free-API strings yourself. Each source writes `02-records/raw/<source>_<YYYYMMDD>.csv`:

```bash
python3 skills/search-export-and-dedup/scripts/api_search.py \
  --openalex-query '<locked OpenAlex string>' --europepmc-query '<locked Europe PMC string>' \
  --pubmed-query '<locked PubMed string>' --semanticscholar-query '<locked S2 string>' \
  --arxiv-query '<locked arXiv string>' \
  --out-dir <project>/02-records/raw --hit-counts <project>/01-search/hit_counts.tsv
```

Omit any source dropped in the locked file (`--sources openalex,europepmc,pubmed`). `--max` (default 2000) caps records per source. Exit 1 means a source failed or hit `--max`: the notes column will show `TRUNCATED` or the count will be `[VERIFY]`. Raise `--max`, narrow the search string with the user, or record why the file is partial. Never report a truncated file as the full search. The script will not overwrite an existing file; to rerun on the same day, use a new folder or move the old file.

Optional extras (only when included in the locked file): Web of Science (Export RIS, `wos_YYYYMMDD.ris`), Scopus (RIS or CSV, `scopus_YYYYMMDD.ris`), Embase (RIS or CSV). The user exports these files; place them in the same folder. A user's own DOI list goes in `02-records/raw/manual_YYYYMMDD.csv` with a `doi,title,year` header and `--source manual`.

Each file's record count must match its row in `hit_counts.tsv` (for API rows, check the "retrieved N of T" note). If it does not match, stop and find out why. Do not drop records to force a match.

3. Checkpoint `exports_complete`. When all files come from `api_search.py` with exit 0, record: `YYYY-MM-DD | search-export-and-dedup | exports_complete (api_search, all sources complete) | agent`. When there are manual exports, ask the user to confirm that the folder contains the full search, and append the line with `| human` only after they confirm.
4. Run dedup from the suite root (the directory that contains `skills/`):

```bash
python3 skills/search-export-and-dedup/scripts/dedup.py \
  --input <project>/02-records/raw/openalex_YYYYMMDD.csv --source openalex \
  --input <project>/02-records/raw/europepmc_YYYYMMDD.csv --source europepmc \
  --input <project>/02-records/raw/pubmed_YYYYMMDD.csv --source pubmed \
  --input <project>/02-records/raw/semanticscholar_YYYYMMDD.csv --source semanticscholar \
  --out-dir <project>/02-records
```

Repeat `--input` / `--source` once per file. Source labels should be stable (`openalex`, `europepmc`, `pubmed`, `semanticscholar`, `arxiv`, `crossref`, and for optional exports `wos`, `scopus`, `embase`). Omit `--source` only if the filename stem is already that label. CSV reading uses pandas when `import pandas` works, otherwise the stdlib `csv` module (`--use-pandas no` forces stdlib).

5. Read `02-records/prisma_counts.json`. Copy `by_source`, `identified_total`, `duplicates_removed`, and `duplicates_removed_by_key` into PRISMA-S items 15 and 16 in `01-search/search_strings.md`. Replace `[VERIFY]` on those two items only.
6. Check the arithmetic: sum of `by_source.*.records_exported` equals `identified_total`; `identified_total` minus `duplicates_removed` equals `records_after_deduplication`. If not, stop. Do not hand-edit the JSON to make it balance.
7. Show the user the per-source counts and the duplicate total. This skill has no lock. Do not start title/abstract screening here.

8. Verify identifiers: After deduplication, open Terminal (macOS) or PowerShell (Windows) and navigate to the suite root (the folder that contains the `skills/` directory). Run:

```bash
python3 skills/search-export-and-dedup/scripts/verify_ids.py <project>/02-records/library.csv
```

Run the same check again on `<project>/evidence/evidence_table.csv` before drafting:

```bash
python3 skills/search-export-and-dedup/scripts/verify_ids.py <project>/evidence/evidence_table.csv
```

This compares remote data against your table without modifying your input file. Open the resulting `identifier_check.csv` in a spreadsheet app. Any non-`ok` status is flagged `[VERIFY]` for you to manually correct in your library. Running with `--offline` skips network calls; format-valid identifiers are marked `unchecked` while badly formed ones are still marked `invalid`.

Match rule used by the script: two records merge on normalized DOI; else on PMID when the DOIs do not conflict; else on normalized title+year when DOI and PMID do not conflict. Title matching lowercases text, turns punctuation into spaces, and requires a four-digit year. A title alone does not match. Details and examples are in `references/dedup_rules.md`.

9. (Optional) Citation snowballing uses OpenAlex (an open catalog of global research) to find backward (articles the seed works cite) and forward (articles citing the seed works) connections based on the seed (starting) articles. Open macOS Terminal or Windows PowerShell and run this from the suite root to find new candidates:

```bash
python3 skills/search-export-and-dedup/scripts/snowball.py <project>/03-screening/included.tsv -o <project>/02-records/raw/snowball_YYYYMMDD.csv
```

If the script exits with code 1 and prints `no seed DOIs found`, no outputs are written. If it exits with code 1 for other errors (meaning an OpenAlex HTTP error or a rate limit that persists after one retry), partial results are saved and the report gets `"incomplete": true`. Exit code 2 means a network failure occurred and no files were written. Optional: configure an API key (a personal access code) as an environment variable (a system setting) named `OPENALEX_API_KEY` for higher limits. To deduplicate these results, add them to the `dedup.py` command using `--input <project>/02-records/raw/snowball_YYYYMMDD.csv --source snowball`. The `LRS_CONTACT_EMAIL` variable is optional, is used only in the OpenAlex mailto and User-Agent, and is never printed. The `--max-forward` flag defaults to 500 forward citations per seed. Seeds that hit the limit are listed under `forward_capped` in the `<out>.json` report. Report these counts in the PRISMA (systematic review reporting standard) identification via other methods column.

## Human gate(s)

No lock. Checkpoint `exports_complete` in `LOG.md` before you treat `library.csv` as the identification set: an agent line when every file came from a complete `api_search.py` run, a human line when manual exports are included.

## Outputs (exact paths + formats)

- `<project>/02-records/raw/` — the `api_search.py` CSVs (columns `title,year,authors,journal,doi,pmid,abstract,pdf_url,source_id`) and any manual exports, unchanged.
- `<project>/02-records/library.csv` — header `record_id,title,year,authors,journal,doi,pmid,abstract,sources,n_copies,identity_key`. One row per kept record. `record_id` is `R0001` upward. `authors` parsed from RIS or NBIB are joined with `; ` (semicolon, space). `sources` joins source labels with `;` and no space, in first-seen order.
- `<project>/02-records/prisma_counts.json` — `by_source` (each source label maps to `records_exported` and `files`), `identified_total`, `skipped_without_identifier`, `duplicates_removed`, `duplicates_removed_by_key` (`doi`, `pmid`, `title_year`), `records_after_deduplication`.

## Quality checklist

- Every locked database has a raw file or a written reason that it was not searched. No API file is truncated without a note.
- JSON arithmetic holds.
- `identity_key` is `doi`, `pmid`, `title_year`, or `none`.
- No record was deleted except as a duplicate under the rule above.
- PRISMA-S items 15 and 16 now quote the JSON, not a rounded number.

## Guardrails

- Do not invent a PMID or DOI to improve a match. The script leaves unknown identifiers empty.
- Do not use a shadow library or a scraped copy of a database.
- Do not exclude records for topic at this step. Off-topic records stay in `library.csv` until screening.
- Do not overwrite raw exports when re-running. Write a new dated file if the search was updated, and say so in the log.

## Next step

`literature-screening`.
