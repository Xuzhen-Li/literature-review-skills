---
name: zotero-library-sync
description: >
  Imports the included records into Zotero, maps them to thematic
  collections, and records a legal full-text route (Unpaywall, publisher,
  institutional access, or interlibrary loan) in pdf_status.csv.   Trigger
  on "add to Zotero", "find the PDFs", "Unpaywall", "full text",
  "collection checklist", or "export notes". Do not use it to screen
  eligibility, to fetch unauthorized copies, or to attach notes before
  the user asks and the reading notes exist.
---

# Zotero library sync

## When to use

`03-screening/included.tsv` exists and `inclusion_lock` is true. This skill tracks legal PDF access. It does not decide inclusion.

## Inputs (paths) / Preconditions

- `<project>/03-screening/included.tsv` and `<project>/02-records/library.csv`.
- The user's Zotero desktop library. Import steps: https://www.zotero.org/support/adding_items_to_zotero
- Collections: https://www.zotero.org/support/collections_and_tags
- Unpaywall API: https://unpaywall.org/products/api
- Crossref metadata when a DOI exists but the title or year is empty: https://www.crossref.org/documentation/retrieve-metadata/
- A contact email the user provides for Unpaywall. Do not invent an email address.
- RIS block shape in `references/ris_template.md`.

## Procedure (numbered steps)

1. Write `04-library/included.ris` with one RIS record per row of `included.tsv`, using `references/ris_template.md` and fields from `library.csv` (abstract, authors, journal). Skip a field that is empty. Do not create a DOI.
2. Tell the user to import that RIS file (Zotero: File, Import) into a new collection named `review-included`. The user clicks through the import. Do not ask them to import the whole pre-screening library into this collection.
3. From the locked scope, propose at most eight thematic collection names. Write them in `04-library/collections.md` as a two-column list: collection name, and the `record_id`s that belong there. A record may sit in more than one collection. The user creates the collections and drags items. Search inside Zotero by DOI or PMID (https://www.zotero.org/support/searching) when the import needs a check.
4. For each included DOI, query Unpaywall. URL-encode nothing inside the DOI path beyond what the docs show; the usual form is:

```text
https://api.unpaywall.org/v2/<doi>?email=<user email>
```

Read `is_oa`, `oa_status` (`gold`, `hybrid`, `green`, `bronze`, `closed`), and `best_oa_location.url_for_pdf` when present. One request at a time. If the API errors, record `oa_status=not_checked` and the error text. Do not retry in a tight loop.

5. Choose a retrieval route in this order, and stop at the first that works. The user performs any login.
   - PDF already attached in their Zotero library.
   - Unpaywall `url_for_pdf` when `is_oa` is true. The user downloads it.
   - The DOI resolver `https://doi.org/<doi>` opened with the user's institutional access.
   - A green repository URL that Unpaywall listed.
   - Interlibrary loan or the user's document-delivery service. Record `requested_ill`. You do not submit the loan unless the user asks, and they send it.
6. If there is no DOI, set `oa_status` to `not_checked` and `notes` to `no DOI`. Try PMID via Zotero "Add Item by Identifier" only to confirm the item exists; still do not invent a DOI. Crossref lookup is for filling a blank title or year on a known DOI (`https://api.crossref.org/works/<doi>`), not for guessing a DOI from a title.
7. Write `04-library/pdf_status.csv` with one row per included `record_id`. Header:

```text
record_id,citation_key,doi,pmid,title,oa_status,pdf_url,retrieval_route,pdf_status,local_path,checked_on,notes
```

`retrieval_route` is `zotero`, `unpaywall`, `publisher`, `repository`, `ill`, or `none`. `pdf_status` is `available`, `requested_ill`, `no_legal_copy_found`, or `user_has_pdf`. `pdf_url` is an Unpaywall, publisher, or repository URL, or empty. `checked_on` is today's date. `local_path` is the path the user gives after they save the file, or empty.

8. Append `YYYY-MM-DD | zotero-library-sync | pdf status written for <N> records | agent`.
9. Write `04-library/collection_checklist.tsv` with the header `theme,record_id,user_confirmed`. Use the theme names from `04-library/collections.md`, at most eight. Every included `record_id` appears at least once. Set `user_confirmed` to `no` until the user checks the list against the collections they created. Do not drive Zotero from desktop control, and do not click through the library for them. When they confirm, set the matching cells to `yes` and run:

```
python3 <suite>/skills/zotero-library-sync/scripts/check_collections.py \
  --checklist <project>/04-library/collection_checklist.tsv \
  --included <project>/03-screening/included.tsv \
  --ready
```

`OK collections` is required before deep reading. Append `YYYY-MM-DD | zotero-library-sync | collection checklist confirmed | human`.
10. Export project notes only after `paper-deep-reading` has written `05-reading/` and the user asks. Do not run this step in the same pass as the PDF status table, and do not log in.

```
python3 <suite>/skills/zotero-library-sync/scripts/export_notes.py \
  --confirm \
  --reading <project>/05-reading \
  --out <project>/04-library/note_export \
  --log <project>/04-library/note_attachment_log.tsv
```

The user attaches each file. The script does not overwrite a copy that is already in `note_export`. After they confirm an attachment, rerun with `--confirm --mark-attached <citation_key> --log <project>/04-library/note_attachment_log.tsv`. The log is the record of what was attached. A missing `record_id` line blocks that export.

## Human gate(s)

No project lock. Stop and ask before any step that needs the user's institutional login or an interlibrary-loan form. Do not store their password.

## Outputs (exact paths + formats)

- `04-library/included.ris`
- `04-library/collections.md`
- `04-library/pdf_status.csv` — header in step 7, one row per included record
- `04-library/collection_checklist.tsv` — `theme`, `record_id`, `user_confirmed`
- `04-library/note_export/` and `04-library/note_attachment_log.tsv` only after the user asks to attach notes

## Quality checklist

- Row count of `pdf_status.csv` equals row count of `included.tsv`.
- Every DOI in the status file matches `included.tsv`.
- `oa_status` is only a value Unpaywall returned, or `not_checked`.
- No URL points at an unauthorized copy. If the user pastes one, refuse to store it and record `no_legal_copy_found`.
- `pdf_url` is empty when `pdf_status` is `no_legal_copy_found` or `requested_ill`.
- `check_collections.py --ready` prints `OK collections` before reading starts.
- A note log exists only after `--confirm`, and it lists no note that was not in `05-reading/`.

## Guardrails

- Do not use shadow libraries, and do not name or link to them as a fallback.
- Do not scrape a publisher PDF behind a login by replaying the user's cookies.
- Do not mark `available` unless the user has the file or an open `url_for_pdf` was returned.
- Do not change screening decisions from this skill.
- Do not attach notes, or overwrite an existing export copy, unless the user asked.

## Next step

`paper-deep-reading` for each included record, after `check_collections.py --ready` prints `OK collections`. A missing PDF does not block a note if the user has another legal copy or chooses to skip that paper; record the skip in `notes` and do not invent findings. Note export waits until those notes exist and the user asks.
