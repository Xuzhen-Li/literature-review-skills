---
name: search-export-and-dedup
description: >
  Collects RIS, PubMed NBIB, and CSV exports of the locked searches, runs
  scripts/dedup.py, and writes library.csv plus PRISMA identification
  counts. Trigger on "export the search", "deduplicate", "merge the RIS
  files", or "PRISMA counts". Do not use it before the search lock, and
  do not use it to screen for eligibility.
---

# Search export and deduplication

## When to use

`gates.search_lock` is true and `01-search/search_strings.md` holds the locked strings. This skill identifies records. Eligibility decisions belong to `literature-screening`.

## Inputs (paths) / Preconditions

- Locked strings and `01-search/hit_counts.tsv`.
- A place to put exports: `<project>/02-records/raw/`.
- `scripts/dedup.py` in this skill directory (follow the symlink to the real path). Tests live in `tests/test_dedup.py`.
- `scripts/verify_ids.py`, tests in `tests/test_verify_ids.py`. Reads `library.csv` or `evidence_table.csv` (a CSV table with `doi` or `pmid` columns). Optional environment variables: `LRS_CONTACT_EMAIL` (polite contact email for Crossref and NCBI queries) and `NCBI_API_KEY` (NCBI key enabling faster request rates); both are optional and never printed.
- The user performs logins. Do not type a password or complete a publisher login.

Browser help is allowed only as the user driving their own session. If no browser is available, give the user the export steps and wait for the files.

## Procedure (numbered steps)

1. Create `<project>/02-records/raw/` if it is missing.
2. One file per database, named `<source>_<YYYYMMDD>.<ext>`:

| Database | Save as | Extension |
|----------|---------|-----------|
| PubMed | Save, format PubMed (https://pubmed.ncbi.nlm.nih.gov/help/) | `.nbib` or `.txt` |
| Web of Science | Export RIS | `.ris` |
| Scopus | Export RIS or CSV | `.ris` or `.csv` |
| Embase, if it was searched | RIS or CSV | `.ris` or `.csv` |

The hit count in `hit_counts.tsv` should match the number of records in that file. If it does not, stop and ask the user which file is complete. Do not drop records to force a match.

3. Ask the user to confirm the raw folder is the full locked search. Append `YYYY-MM-DD | search-export-and-dedup | exports_complete | human` only after they say yes.
4. Run dedup from the suite root (the directory that contains `skills/`):

```bash
python3 skills/search-export-and-dedup/scripts/dedup.py \
  --input <project>/02-records/raw/pubmed_YYYYMMDD.nbib --source pubmed \
  --input <project>/02-records/raw/wos_YYYYMMDD.ris --source wos \
  --input <project>/02-records/raw/scopus_YYYYMMDD.csv --source scopus \
  --out-dir <project>/02-records
```

Repeat `--input` / `--source` once per file. Source labels should be stable (`pubmed`, `wos`, `scopus`, `embase`). Omit `--source` only if the filename stem is already that label. CSV reading uses pandas when `import pandas` works, otherwise the stdlib `csv` module (`--use-pandas no` forces stdlib).

5. Read `02-records/prisma_counts.json`. Copy `by_source`, `identified_total`, `duplicates_removed`, and `duplicates_removed_by_key` into PRISMA-S items 15 and 16 in `01-search/search_strings.md`. Replace `[VERIFY]` on those two items only.
6. Check the arithmetic: sum of `by_source.*.records_exported` equals `identified_total`; `identified_total` minus `duplicates_removed` equals `records_after_deduplication`. If not, stop. Do not hand-edit the JSON to make it balance.
7. Show the user the per-source counts and the duplicate total. This skill has no lock. Do not start title/abstract screening here.

8. Verify identifiers: After deduplication, open Terminal (macOS) or Command Prompt/Terminal (Windows) and navigate to the suite root (the folder that contains the `skills/` directory). Run:

```bash
python3 skills/search-export-and-dedup/scripts/verify_ids.py <project>/02-records/library.csv
```

This compares remote data against your table without modifying your input file. Open the resulting `identifier_check.csv` in a spreadsheet app. Any non-`ok` status is flagged `[VERIFY]` for you to manually correct in your library. Running with `--offline` skips network calls; format-valid identifiers are marked `unchecked` while badly formed ones are still marked `invalid`.

Match rule used by the script: two records merge on normalized DOI; else on PMID when the DOIs do not conflict; else on normalized title+year when DOI and PMID do not conflict. Title matching lowercases text, turns punctuation into spaces, and requires a four-digit year. A title alone does not match. Details and examples are in `references/dedup_rules.md`.

## Human gate(s)

No lock. Checkpoint: the user confirms the exports are complete before you treat `library.csv` as the identification set. Record `exports_complete` in `LOG.md`.

## Outputs (exact paths + formats)

- `<project>/02-records/raw/` — the export files, unchanged.
- `<project>/02-records/library.csv` — header `record_id,title,year,authors,journal,doi,pmid,abstract,sources,n_copies,identity_key`. One row per kept record. `record_id` is `R0001` upward. `authors` parsed from RIS or NBIB are joined with `; ` (semicolon, space). `sources` joins source labels with `;` and no space, in first-seen order.
- `<project>/02-records/prisma_counts.json` — `by_source` (each source label maps to `records_exported` and `files`), `identified_total`, `skipped_without_identifier`, `duplicates_removed`, `duplicates_removed_by_key` (`doi`, `pmid`, `title_year`), `records_after_deduplication`.

## Quality checklist

- Every locked database has a raw file or a written reason that it was not searched.
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
