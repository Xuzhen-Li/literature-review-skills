---
name: zotero-library-sync
description: >
  Imports the included records into Zotero, maps them to thematic
  collections, and records a legal full-text route (Unpaywall, publisher,
  institutional access, or interlibrary loan) in pdf_status.csv. Trigger
  on "add to Zotero", "find the PDFs", "Unpaywall", or "full text".
  Do not use it to screen eligibility or to fetch unauthorized copies.
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

## Human gate(s)

No project lock. Stop and ask before any step that needs the user's institutional login or an interlibrary-loan form. Do not store their password.

## Outputs (exact paths + formats)

- `04-library/included.ris`
- `04-library/collections.md`
- `04-library/pdf_status.csv` — header in step 7, one row per included record

## Quality checklist

- Row count of `pdf_status.csv` equals row count of `included.tsv`.
- Every DOI in the status file matches `included.tsv`.
- `oa_status` is only a value Unpaywall returned, or `not_checked`.
- No URL points at an unauthorized copy. If the user pastes one, refuse to store it and record `no_legal_copy_found`.
- `pdf_url` is empty when `pdf_status` is `no_legal_copy_found` or `requested_ill`.

## Guardrails

- Do not use shadow libraries, and do not name or link to them as a fallback.
- Do not scrape a publisher PDF behind a login by replaying the user's cookies.
- Do not mark `available` unless the user has the file or an open `url_for_pdf` was returned.
- Do not change screening decisions from this skill.

## Next step

`paper-deep-reading` for each included record. A missing PDF does not block a note if the user has another legal copy or chooses to skip that paper; record the skip in `notes` and do not invent findings.
