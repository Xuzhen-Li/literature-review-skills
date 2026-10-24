---
name: zotero-library-sync
description: >
  Imports the included records into Zotero, maps them to thematic
  collections, and records a legal full-text route (Unpaywall, publisher,
  institutional access, interlibrary loan, or a PDF the user uploads)
  in pdf_status.csv. Trigger on "add to Zotero", "find the PDFs",
  "Unpaywall", "full text", "collection checklist", or "export notes".
  Do not use it to screen eligibility, to fetch unauthorized copies, or
  to attach notes before the user asks and the reading notes exist.
---

# Zotero library sync

## Opening

On first use in a project, say this verbatim:

I am Zotero library sync. I record a legal route for each included paper, and when this computer cannot download it I give you the DOI to upload.

## When to use

`03-screening/included.tsv` exists and `inclusion_lock` is true. This skill tracks legal PDF access. It does not decide inclusion.

## Inputs (paths) / Preconditions

- `<project>/03-screening/included.tsv` and `<project>/02-records/library.csv`.
- Optional: the user's Zotero desktop library (steps 1-3 and 10). Without Zotero, skip the RIS import and collections; `find_oa_pdfs.py` and `pdf_handoff.py` still work. Import steps: https://www.zotero.org/support/adding_items_to_zotero
- Collections: https://www.zotero.org/support/collections_and_tags
- Unpaywall API: https://unpaywall.org/products/api
- Crossref metadata when a DOI exists but the title or year is empty: https://www.crossref.org/documentation/retrieve-metadata/
- A contact email the user provides for Unpaywall. Do not invent an email address.
- RIS block shape in `references/ris_template.md`.

## Procedure (numbered steps)

1. Write `04-library/included.ris` with one RIS record per row of `included.tsv`, using `references/ris_template.md` and fields from `library.csv` (abstract, authors, journal). Skip a field that is empty. Do not create a DOI.
2. Tell the user to import that RIS file (Zotero: File, Import) into a new collection named `review-included`. The user clicks through the import. Do not ask them to import the whole pre-screening library into this collection.
3. From the locked scope, propose at most eight thematic collection names. Write them in `04-library/collections.md` as a two-column list: collection name, and the `record_id`s that belong there. A record may sit in more than one collection. The user creates the collections and drags items. Search inside Zotero by DOI or PMID (https://www.zotero.org/support/searching) when the import needs a check.
4. Fast path (no account, no API key, no Zotero needed): run the open-access finder on the included list. It asks OpenAlex first and Unpaywall only when `LRS_CONTACT_EMAIL` is set, and saves only legal OA PDFs:

```bash
python3 <suite>/skills/zotero-library-sync/scripts/find_oa_pdfs.py \
  <project>/03-screening/included.tsv \
  -o <project>/04-library/oa_check.csv \
  --download <project>/04-library/uploads
```

Saved files are named `<record_id>-<hash>.pdf`, so copy `local_path` straight into `pdf_status.csv` (do not rely on `pdf_handoff.py accept` for them). It refuses to overwrite `-o` without `--force`, downloads only http/https links up to 100 MB, and exits 1 when a lookup or download failed. Use its `oa_status`, `pdf_url`, and `local_path` columns to fill `pdf_status.csv` (step 7): a saved file is `user_has_pdf` with `retrieval_route` `unpaywall` or `repository`; `closed` rows go to the upload list in step 8. If the script cannot reach the network, fall back to the manual Unpaywall query below. Manual query, one DOI at a time: URL-encode nothing inside the DOI path beyond what the docs show; the usual form is:

```text
https://api.unpaywall.org/v2/<doi>?email=<user email>
```

Read `is_oa`, `oa_status` (`gold`, `hybrid`, `green`, `bronze`, `closed`), and `best_oa_location.url_for_pdf` when present. One request at a time. If the API errors, record `oa_status=not_checked` and the error text. Do not retry in a tight loop.

5. Try the agent browser first. If it is not logged in, or the browser tool fails, use computer control of the user's own desktop browser when that tool is available. The user types any password, captcha, or second factor. Do not ask for those values, do not type them, and do not store them.
6. Choose a retrieval route in this order, and stop at the first that works.
   - PDF already attached in their Zotero library, or already in `04-library/uploads/`.
   - Unpaywall `url_for_pdf` when `is_oa` is true. The user downloads it.
   - The DOI resolver `https://doi.org/<doi>` when `download_access` is `institutional`. Skip this route for `open_access` and `unavailable`.
   - A green repository URL that Unpaywall listed.
   - If the page refuses the download, the session has no entitlement, or `download_access` is `unavailable`, stop. Set `pdf_status` to `awaiting_user_upload`. Do not keep driving the desktop to reach a copy, and do not open a shadow library.
   - Interlibrary loan or the user's document-delivery service, only when they ask. Record `requested_ill`. They send the request.
If there is no DOI, set `oa_status` to `not_checked` and `notes` to `no DOI`. Try PMID via Zotero "Add Item by Identifier" only to confirm the item exists; still do not invent a DOI. Crossref lookup is for filling a blank title or year on a known DOI (`https://api.crossref.org/works/<doi>`), not for guessing a DOI from a title. A row with no DOI can still be uploaded by the user; leave `doi` empty in the list.
7. Write `04-library/pdf_status.csv` with one row per included `record_id`. Header:

```text
record_id,citation_key,doi,pmid,title,oa_status,pdf_url,retrieval_route,pdf_status,local_path,checked_on,notes
```

`retrieval_route` is `zotero`, `unpaywall`, `publisher`, `repository`, `ill`, `user_upload`, or `none`. `pdf_status` is `available`, `requested_ill`, `no_legal_copy_found`, `user_has_pdf`, `awaiting_user_upload`, or `user_uploaded`. `pdf_url` is an Unpaywall, publisher, or repository URL, or empty. `checked_on` is today's date. `local_path` is the path the user gives after they save the file, or empty.

8. For every `awaiting_user_upload` or `no_download_permission` row, write the DOI list and show it to the user. They save each PDF at the `save_as` path. You do not download it.

```bash
python3 <suite>/skills/zotero-library-sync/scripts/pdf_handoff.py write \
  --status <project>/04-library/pdf_status.csv \
  --out <project>/04-library/doi_for_upload.tsv
python3 <suite>/skills/zotero-library-sync/scripts/pdf_handoff.py accept \
  --status <project>/04-library/pdf_status.csv \
  --uploads <project>/04-library/uploads \
  --out <project>/04-library/pdf_status.csv
```

`accept` changes a row to `user_uploaded` only when `04-library/uploads/<record_id>.pdf` is a non-empty PDF. Leave the other rows waiting.
9. Append `YYYY-MM-DD | zotero-library-sync | pdf status written for <N> records | agent`.
10. Write `04-library/collection_checklist.tsv` with the header `theme,record_id,user_confirmed`. Use the theme names from `04-library/collections.md`, at most eight. Every included `record_id` appears at least once. Set `user_confirmed` to `no` until the user checks the list against the collections they created. Desktop control may open the database homepage or a download page. It does not click through Zotero for them, and it does not type credentials. When they confirm, set the matching cells to `yes` and run:

```
python3 <suite>/skills/zotero-library-sync/scripts/check_collections.py \
  --checklist <project>/04-library/collection_checklist.tsv \
  --included <project>/03-screening/included.tsv \
  --ready
```

`OK collections` is required before deep reading. Append `YYYY-MM-DD | zotero-library-sync | collection checklist confirmed | human`.
11. Export project notes only after `paper-deep-reading` has written `05-reading/` and the user asks. Do not run this step in the same pass as the PDF status table, and do not log in.

```
python3 <suite>/skills/zotero-library-sync/scripts/export_notes.py \
  --confirm \
  --reading <project>/05-reading \
  --out <project>/04-library/note_export \
  --log <project>/04-library/note_attachment_log.tsv
```

The user attaches each file. The script does not overwrite a copy that is already in `note_export`. After they confirm an attachment, rerun with `--confirm --mark-attached <citation_key> --log <project>/04-library/note_attachment_log.tsv`. The log is the record of what was attached. A missing `record_id` line blocks that export.

## Human gate(s)

No project lock. Stop when a paper cannot be downloaded and hand the user `doi_for_upload.tsv`. Do not store their password.

## Outputs (exact paths + formats)

- `04-library/included.ris`
- `04-library/collections.md`
- `04-library/pdf_status.csv` — header in step 7, one row per included record
- `04-library/doi_for_upload.tsv` — `record_id`, `doi`, `title`, `save_as`, when a download is not permitted
- `04-library/uploads/<record_id>.pdf` — placed by the user
- `04-library/collection_checklist.tsv` — `theme`, `record_id`, `user_confirmed`
- `04-library/note_export/` and `04-library/note_attachment_log.tsv` only after the user asks to attach notes

## Quality checklist

- Row count of `pdf_status.csv` equals row count of `included.tsv`.
- Every DOI in the status file matches `included.tsv`.
- `oa_status` is only a value OpenAlex or Unpaywall returned, or `not_checked`.
- No URL points at an unauthorized copy. If the user pastes one, refuse to store it and record `no_legal_copy_found`.
- `pdf_url` is empty when `pdf_status` is `no_legal_copy_found` or `requested_ill`.
- `check_collections.py --ready` prints `OK collections` before reading starts.
- A note log exists only after `--confirm`, and it lists no note that was not in `05-reading/`.

## Guardrails

- Do not use shadow libraries, and do not name or link to them as a fallback.
- Do not scrape a publisher PDF behind a login by replaying the user's cookies.
- When the computer has no download permission, give the DOI and wait for the upload. Do not fetch the URL yourself.
- Do not mark `available` unless the user has the file or an open `url_for_pdf` was returned.
- Do not change screening decisions from this skill.
- Do not attach notes, or overwrite an existing export copy, unless the user asked.

## Next step

`paper-deep-reading` for each included record, after `check_collections.py --ready` prints `OK collections`. A missing PDF does not block a note if the user has another legal copy or chooses to skip that paper; record the skip in `notes` and do not invent findings. Note export waits until those notes exist and the user asks.
