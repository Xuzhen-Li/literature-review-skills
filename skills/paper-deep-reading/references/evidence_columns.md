# Evidence columns

Header row for `evidence/evidence_table.csv`. This is the same header as `shared/evidence_table_schema.md`.

```text
evidence_id,record_id,citation_key,doi,pmid,year,venue,first_author,n_authors,study_design,setting,method_note,finding,statistic,page,quote,limitations,supports_claim,claim_strength,outline_section,note_path,added
```

- `evidence_id`: `E001`, `E002`, ... Do not renumber.
- `study_design`: `rct`, `cohort`, `case-control`, `cross-sectional`, `qualitative`, `in-vitro`, `in-silico`, `systematic-review`, `scoping-review`, `narrative-review`, `overview-of-reviews`, `methods`, `other`.
- `claim_strength`: `direct`, `indirect`, `conflicting`, `background`.
- `page`: required. `quote`: empty, or one sentence.
- `outline_section`: leave empty. The outline skill fills it.
- `note_path`: `05-reading/<citation_key>.md`.
- `added`: `YYYY-MM-DD`.
- `n_authors`: integer or empty. Do not guess. Draft citations use it for `et al.` (3 or more), `and` (2), or a single name (1).

Identifiers must match `02-records/library.csv` for the same `record_id`. If they do not, do not append the row.
