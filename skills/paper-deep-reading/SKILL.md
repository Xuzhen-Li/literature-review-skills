---
name: paper-deep-reading
description: >
  Writes one structured note per included paper and appends findings to
  the evidence table with page locators and no invented identifiers.
  Trigger on "read this paper", "deep read", "evidence table", or
  "paper note". Do not use it to outline the review, draft a section,
  or summarize a paper you cannot open.
---

# Paper deep reading

## Opening

On first use in a project, say this verbatim:

I am paper deep reading. I write a note and evidence rows only from a file you hold, and I do not invent page numbers.

## When to use

An included record has a legal PDF or other full text the user can open (`04-library/pdf_status.csv` status `available`, `user_has_pdf`, or `user_uploaded`). Read one paper at a time. If the status is `no_legal_copy_found`, `awaiting_user_upload`, or `requested_ill`, log a no-PDF skip for that record and move on; do not wait for the user's upload. When the file arrives later, read it then. Do not read from an abstract alone and call it a deep read.

## Inputs (paths) / Preconditions

- `<project>/03-screening/included.tsv` and `<project>/04-library/pdf_status.csv`.
- Only when `use_zotero` is `true` in `project.yaml`: `<project>/04-library/collection_checklist.tsv` with every `user_confirmed` cell `yes`. Do not start while `check_collections.py --ready` would fail.
- `<project>/02-records/library.csv` for DOI, PMID, authors, and `journal`. Copy `journal` into the evidence column `venue` and into the note's `venue` line. `03-screening/included.tsv` already stores that same value as `venue`.
- The user's open copy of the paper.
- Column rules in `references/evidence_columns.md` (same header as `shared/evidence_table_schema.md`).
- Note skeleton in `references/paper_note_template.md`.

## Procedure (numbered steps)

1. Pick the next included `record_id` that has no `05-reading/<citation_key>.md`. Open the PDF the user supplied. If a DOI or PMID on the PDF differs from `library.csv`, stop and mark the note `[VERIFY]`. Do not "fix" the library by typing a new DOI.
2. Create `05-reading/<citation_key>.md` from the template. Fill bibliographic fields from the library and the PDF first page. `n_authors` is a count you can see, or empty.
3. Write the aim, the design (one label from the evidence schema: `rct`, `cohort`, `case-control`, `cross-sectional`, `qualitative`, `in-vitro`, `in-silico`, `systematic-review`, `scoping-review`, `narrative-review`, `overview-of-reviews`, `methods`, `other`), and the setting, only when the paper states them.
4. For each finding you may later want to cite, add one evidence row, not a paragraph of mixed claims. Each row needs `page` (printed page, section, or figure/table id). A number you did not see on that page does not go in `statistic`.
5. Quotes: leave `quote` empty by default. If a short sentence is worth keeping, copy at most one sentence and put the page in `page`. Paraphrase everything else.
6. Limitations: only those the paper states. If you see a limitation the authors do not mention, put it under `Reader note` in the markdown file, not in the `limitations` column.
7. Figure ideas: describe an original schematic this review could draw. Name the published figure as something not to copy (`Do not copy: Fig. 2 of this paper`). Do not trace it.
8. Append rows to `evidence/evidence_table.csv`. If the file is missing, write the header from `references/evidence_columns.md` first. `evidence_id` starts at `E001`. The next id is one above the current maximum, zero-padded to at least three digits. Never reuse or renumber an id.
9. Set `supports_claim` to the claim this row can actually support, and `claim_strength` to `direct`, `indirect`, `conflicting`, or `background`. A result that disagrees with the locked question's expected direction is `conflicting`, and it is still appended.
10. Append `YYYY-MM-DD | paper-deep-reading | note <citation_key> with <k> evidence rows | agent`.

## Human gate(s)

No project lock. Stop when the PDF and the library record disagree on DOI, PMID, or year, and ask the user which source to trust. Do not continue that paper until they answer.

## Outputs (exact paths + formats)

- `05-reading/<citation_key>.md` — template sections, including the line `record_id: R0001` near the top.
- `evidence/evidence_table.csv` — appended rows only. Header in `references/evidence_columns.md`.

## Quality checklist

- The note's `record_id`, DOI, and PMID match `library.csv` or are marked `[VERIFY]` with the work stopped.
- Every finding row has a page locator and a `claim_strength`.
- `statistic` is empty or a verbatim fragment from that page.
- `quote` is empty or a single sentence.
- No evidence id was reused. The CSV still parses (commas inside fields are quoted).

## Guardrails

- Do not deep-read from the abstract, a blog, or a citation manager snippet.
- Do not invent sample size, p values, or effect directions.
- Do not paste long quotations. One sentence is the maximum, and only with a page.
- Do not add a row for a paper that is not in `included.tsv`.
- Do not delete an evidence row. A correction is a new row whose `method_note` is `corrects E014`.

## Next step

The next unread included paper. When every included record is either noted or logged as skipped for lack of a legal copy, go to `exemplar-review-analysis`. Attaching a note inside the user's reference manager is optional, and only after they ask: that export is `zotero-library-sync`, with a log of what was attached.
