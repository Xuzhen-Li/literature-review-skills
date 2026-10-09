# Evidence table schema

Path: `<project>/evidence/evidence_table.csv`

UTF-8, comma-separated, one header row, one finding per row. Append rows. Never reuse an `evidence_id` and never edit a row to support a new claim. If a finding was wrong, leave the old row unchanged and append a correction row whose `method_note` is `corrects E007` (use the real id).

`paper-deep-reading` creates the file if it is missing and is the only skill that adds rows. Later skills may fill `outline_section`. They do not add findings.

## Header

```text
evidence_id,record_id,citation_key,doi,pmid,year,venue,first_author,n_authors,study_design,setting,method_note,finding,statistic,page,quote,limitations,supports_claim,claim_strength,outline_section,note_path,added
```

## Columns

| Column | Required | Rule |
|--------|----------|------|
| `evidence_id` | yes | `E` plus digits, at least three digits, starting at `E001`. Next id is one above the current maximum, zero-padded to the same width (`E099` then `E100`). |
| `record_id` | yes | `R` id from `02-records/library.csv`. The row must match that record. |
| `citation_key` | yes | `FirstAuthorLast` + year, ASCII letters and digits only, for example `Lovelace2020`. Disambiguate collisions with a trailing `a`, `b`, `c`. |
| `doi` | no | Normalized lowercase DOI, or empty. Must match `library.csv` for this `record_id` when either side has a DOI. |
| `pmid` | no | Digits only, or empty. Must match `library.csv` when either side has a PMID. |
| `year` | yes | Four-digit publication year from the record. |
| `venue` | no | Journal or source title copied from the `journal` column of `02-records/library.csv`. Leave empty if the export had none. Do not guess. |
| `first_author` | yes | Family name as printed on the paper. If it is unreadable, use `Anon` and set the note status to `[VERIFY]`. |
| `n_authors` | no | Integer count of authors on the paper, from the export or the PDF. Empty if unknown. Do not guess. Citation style uses this count: 1 author, 2 authors (`and`), 3 or more (`et al.`). |
| `study_design` | yes | One of: `rct`, `cohort`, `case-control`, `cross-sectional`, `qualitative`, `in-vitro`, `in-silico`, `systematic-review`, `scoping-review`, `narrative-review`, `overview-of-reviews`, `methods`, `other`. |
| `setting` | no | Population, species, system, or context in a few words. |
| `method_note` | no | One short clause (sample size, assay, model). Not a second finding. |
| `finding` | yes | One paraphrased sentence. No citation keys inside the sentence. |
| `statistic` | no | Effect, interval, n, or p value only when the source prints it. Copy the source text. Leave empty rather than recalculating. |
| `page` | yes | Page, section, or figure/table id where the finding appears (`p. 4`, `Table 2`, `Fig. 1`). |
| `quote` | no | Empty unless a short quotation is necessary. At most one sentence, with the page in `page`. |
| `limitations` | no | A limitation the source authors state, or empty. Do not invent one. |
| `supports_claim` | yes | The review claim this row is allowed to support. One sentence. |
| `claim_strength` | yes | `direct`, `indirect`, `conflicting`, or `background`. |
| `outline_section` | no | Filled by `review-outline-builder`. Empty until then. |
| `note_path` | yes | `05-reading/<citation_key>.md` |
| `added` | yes | ISO date `YYYY-MM-DD` when the row was appended. |

## Claim strength

- `direct`: the source measured or synthesized the claim in `supports_claim`.
- `indirect`: the source bears on a related question; the review must not phrase it as a direct result.
- `conflicting`: the source reports a result that disagrees with the claim. Keep these rows. Do not drop them.
- `background`: definition, method, or scope only. Not evidence for an empirical claim.

## Identifier check

Before appending, confirm `doi` and `pmid` against `library.csv`. If they disagree, stop and mark the note `[VERIFY]`. Do not invent a DOI, PMID, author, year, or journal.

Placeholder tokens in examples (`10.xxxx/xxxxx`) are not citations and must not be copied into the table.

## Draft binding

Every factual sentence in `09-draft/` and `10-polish/` maps to one or more `evidence_id` values, or ends with `[NEEDS SOURCE]`. `[NEEDS SOURCE]` is allowed in a draft. It is not allowed in a submitted manuscript. An evidence row itself always points at a library record.
