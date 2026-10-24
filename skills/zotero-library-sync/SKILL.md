---
name: zotero-library-sync
description: >
  Gets full texts for included papers itself: finds and downloads
  legal open-access PDFs (OpenAlex, Unpaywall, Europe PMC, Semantic
  Scholar, arXiv), records each route in pdf_status.csv, and gives the
  user only a short ranked please-fetch list of essential papers it could
  not get. Zotero import and collections are optional. Trigger on "find
  the PDFs", "full text", "download the papers", "please fetch", "add to
  Zotero", "collection checklist", or "export notes". Do not use it to
  screen eligibility, to fetch unauthorized copies, or to attach notes
  before the user asks and the reading notes exist.
---

# Zotero library sync

## Opening

On first use in a project, say this verbatim:

I am Zotero library sync. I download open-access full texts myself. You only get a short list of the essential papers I could not get, with each DOI and why it matters. Zotero is optional.

## When to use

`03-screening/included.tsv` exists and `inclusion_lock` is true. This skill gets legal full text. It does not decide inclusion.

## Inputs (paths) / Preconditions

- `<project>/03-screening/included.tsv` and `<project>/02-records/library.csv`.
- `<project>/project.yaml`: `download_access` (default `open_access`) and `use_zotero` (default `false`).
- `scripts/find_oa_pdfs.py`, `scripts/please_fetch.py`, `scripts/pdf_handoff.py`. No account or key is needed. `LRS_CONTACT_EMAIL` turns on Unpaywall (it requires an email the user gave; do not invent one). `S2_API_KEY` is optional.
- Optional, only when `use_zotero` is `true`: the user's Zotero desktop library (https://www.zotero.org/support/adding_items_to_zotero, https://www.zotero.org/support/collections_and_tags) and the RIS block shape in `references/ris_template.md`.
- Crossref metadata when a DOI exists but the title or year is empty: https://www.crossref.org/documentation/retrieve-metadata/

## Procedure (numbered steps)

1. Download the open-access PDFs yourself. No login, no Zotero:

```bash
python3 <suite>/skills/zotero-library-sync/scripts/find_oa_pdfs.py \
  <project>/03-screening/included.tsv \
  -o <project>/04-library/oa_check.csv \
  --download <project>/04-library/pdfs
```

It asks OpenAlex, Unpaywall (only with `LRS_CONTACT_EMAIL`), Europe PMC, Semantic Scholar, and arXiv in that order. When a download fails it tries the next source's link. It saves only legal OA copies (http/https, up to 100 MB) as `<record_id>-<hash>.pdf`, never overwrites a file, and refuses to overwrite `-o` without `--force`. Exit 1 means a lookup or download failed for some rows; the rows are still written. Run it again later for those rows before treating them as closed.
2. Write `04-library/pdf_status.csv` with one row per included `record_id`. Header:

```text
record_id,citation_key,doi,pmid,title,oa_status,pdf_url,retrieval_route,pdf_status,local_path,checked_on,notes
```

Copy `oa_status`, `pdf_url`, and `local_path` from `oa_check.csv`. A saved file is `pdf_status` `user_has_pdf` with `retrieval_route` `unpaywall` or `repository` (`repository` covers Europe PMC, Semantic Scholar, and arXiv; name the source in `notes`). A row with no saved file is `no_legal_copy_found` with route `none`. When `download_access` is `institutional`, you may first try `https://doi.org/<doi>` in the logged-in browser (route `publisher`); the user types any password, captcha, or second factor, never you. `retrieval_route` is `zotero`, `unpaywall`, `publisher`, `repository`, `ill`, `user_upload`, or `none`. `pdf_status` is `available`, `requested_ill`, `no_legal_copy_found`, `user_has_pdf`, `awaiting_user_upload`, or `user_uploaded`. `checked_on` is today's date. If there is no DOI, set `oa_status` to `not_checked` and `notes` to `no DOI`; do not invent a DOI. Crossref is for filling a blank title or year on a known DOI (`https://api.crossref.org/works/<doi>`), not for guessing one.
3. Triage every included paper that has no PDF. Write `04-library/fulltext_need.tsv` with the header `record_id,doi,need,why,rank`:
   - `essential`: the review cannot be written honestly from the abstract alone. For example, it is a core study whose methods, effect sizes, or figures you must read, the only source for a claim in the locked scope, or a key paper that defines the field. `why` is one clear sentence for the user, and `rank` starts at 1 for the most important paper.
   - `useful`: the full text would help, but the abstract is enough to make the point.
   - `abstract_ok`: the abstract is enough for how the review uses this paper.
   Keep the `essential` list short. Rank papers by how much the review depends on them. Do not mark a paper `essential` just because it is closed access.
4. Build the please-fetch list:

```bash
python3 <suite>/skills/zotero-library-sync/scripts/please_fetch.py \
  --status <project>/04-library/oa_check.csv \
  --need <project>/04-library/fulltext_need.tsv \
  --uploads <project>/04-library/uploads \
  --out-dir <project>/04-library
```

This lists only `essential` papers that still have no PDF and are not yet in `uploads/`, ranked, up to `--max` (default 15). All other missing papers go to `abstract_only.tsv`. Exit 2 means a missing paper has no triage row, or a triage row is malformed; fix `fulltext_need.tsv` and run the script again. If essential papers exceed `--max`, tighten your ranking instead of raising the cap.
5. Show the user `04-library/please_fetch.md` as is: the numbered DOIs, why each paper matters, and the file name `04-library/uploads/<record_id>.pdf` to save it under. Do not ask them to fetch anything else. If the list is empty, say so and move on. Do not wait for uploads: continue reading, and cite any paper that never arrives from its abstract only.
6. When the user says they saved files, record them:

```bash
python3 <suite>/skills/zotero-library-sync/scripts/pdf_handoff.py accept \
  --status <project>/04-library/pdf_status.csv \
  --uploads <project>/04-library/uploads \
  --out <project>/04-library/pdf_status.csv
```

`accept` changes `awaiting_user_upload` or `no_download_permission` rows only, so first set the please-fetch rows to `awaiting_user_upload`. Then rerun step 4 so the list shrinks. `pdf_handoff.py write` still makes the older `doi_for_upload.tsv` for every closed paper; use it only when the user asks for the full list.
7. Append `YYYY-MM-DD | zotero-library-sync | pdf status written for <N> records; please_fetch <K>; abstract_only <M> | agent`.
8. Optional, only when `use_zotero` is `true`. Write `04-library/included.ris` with one record per row of `included.tsv` (`references/ris_template.md`, fields from `library.csv`, empty fields skipped, no invented DOI). The user imports it into a collection named `review-included`. Propose at most eight theme collections in `04-library/collections.md` (collection name, `record_id`s). Write `04-library/collection_checklist.tsv` with the header `theme,record_id,user_confirmed`, every included `record_id` at least once, `user_confirmed` `no` until the user checks it. When they confirm, set the cells to `yes` and run:

```
python3 <suite>/skills/zotero-library-sync/scripts/check_collections.py \
  --checklist <project>/04-library/collection_checklist.tsv \
  --included <project>/03-screening/included.tsv \
  --ready
```

Append `YYYY-MM-DD | zotero-library-sync | collection checklist confirmed | human` after `OK collections`. Do not click through Zotero for the user or type credentials.
9. Export project notes only after `paper-deep-reading` has written `05-reading/` and the user asks. Do not run this step in the same pass as the PDF status table, and do not log in.

```
python3 <suite>/skills/zotero-library-sync/scripts/export_notes.py \
  --confirm \
  --reading <project>/05-reading \
  --out <project>/04-library/note_export \
  --log <project>/04-library/note_attachment_log.tsv
```

The user attaches each file. The script does not overwrite a copy that is already in `note_export`. After they confirm an attachment, rerun with `--confirm --mark-attached <citation_key> --log <project>/04-library/note_attachment_log.tsv`. A missing `record_id` line blocks that export.

## Human gate(s)

No project lock and no wait. The user is asked only for the papers on `please_fetch.md`. When `use_zotero` is `true`, `collection_checklist_confirmed` is a checkpoint. Do not ask for or store a password.

## Outputs (exact paths + formats)

- `04-library/oa_check.csv` and `04-library/pdfs/<record_id>-<hash>.pdf` — written by `find_oa_pdfs.py`
- `04-library/pdf_status.csv` — header in step 2, one row per included record
- `04-library/fulltext_need.tsv` — `record_id`, `doi`, `need`, `why`, `rank`, one row per included paper without a PDF
- `04-library/please_fetch.md` and `please_fetch.tsv` — the ranked list for the user (`priority`, `record_id`, `doi`, `title`, `why`, `save_as`, `landing_url`)
- `04-library/abstract_only.tsv` — missing papers read from the abstract; report them as a limitation
- `04-library/uploads/<record_id>.pdf` — placed by the user
- Only when `use_zotero` is `true`: `04-library/included.ris`, `04-library/collections.md`, `04-library/collection_checklist.tsv` (`theme`, `record_id`, `user_confirmed`)
- `04-library/doi_for_upload.tsv` only when the user asks for every closed DOI
- `04-library/note_export/` and `04-library/note_attachment_log.tsv` only after the user asks to attach notes

## Quality checklist

- Row count of `pdf_status.csv` equals row count of `included.tsv`.
- Every DOI in the status file matches `included.tsv`.
- `oa_status` is only a value OpenAlex or Unpaywall returned, or `not_checked`.
- No URL points at an unauthorized copy. If the user pastes one, refuse to store it and record `no_legal_copy_found`.
- `pdf_url` is empty when `pdf_status` is `no_legal_copy_found` or `requested_ill`.
- `please_fetch.md` lists only `essential` papers without a PDF, ranked, each with a DOI (or `no DOI`) and a reason.
- When `use_zotero` is `true`, `check_collections.py --ready` prints `OK collections`.
- A note log exists only after `--confirm`, and it lists no note that was not in `05-reading/`.

## Guardrails

- Do not use shadow libraries, and do not name or link to them as a fallback.
- Do not scrape a publisher PDF behind a login by replaying the user's cookies.
- Do not hand the user a paper you could get yourself, or a paper that is not essential. Do not fetch a closed paper through a route the user has not authorized.
- Do not mark `available` unless the user has the file or an open `url_for_pdf` was returned.
- Do not change screening decisions from this skill.
- Do not attach notes, or overwrite an existing export copy, unless the user asked.

## Next step

`paper-deep-reading` for each included record once `pdf_status.csv`, `fulltext_need.tsv`, and `please_fetch.md` exist (and, when `use_zotero` is `true`, after `OK collections`). A missing PDF does not block reading: `paper-deep-reading` logs a no-PDF skip for that record, and the review cites it from its abstract only, as listed in `abstract_only.tsv`. Do not invent findings. Note export waits until those notes exist and the user asks.
