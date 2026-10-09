# PRISMA 2020 flow

Replace every `n`. Use the box names from the PRISMA 2020 flow diagram (https://www.prisma-statement.org/). Leave an unused other-source line as `n=0` and say why it is zero. Do not omit the line.

## Identification

| Box | n | Source of the number |
|-----|---|----------------------|
| Records identified from databases | | Sum of `records_exported` inside `by_source` for database sources |
| Records identified from registers | | Sum of `records_exported` for register sources, or 0 |
| Records identified from websites | | Count, or 0 |
| Records identified from organisations | | Count, or 0 |
| Records identified from citation searching | | Count, or 0 |
| Duplicate records removed | | `duplicates_removed` |
| Records marked as ineligible by automation tools | | 0 unless a tool was used and the user logged it |
| Records removed for other reasons | | 0 unless listed with reasons |

## Screening (databases and registers)

| Box | n | Source of the number |
|-----|---|----------------------|
| Records screened (title/abstract) | | `records_after_deduplication` minus automation and other removals |
| Records excluded (title/abstract) | | `consensus=exclude` at stage `title_abstract` |
| Reports sought for retrieval | | screened minus title/abstract exclusions |
| Reports not retrieved | | `FT_NOT_RETRIEVED` |
| Reports assessed for eligibility | | sought minus not retrieved |
| Reports excluded | | full-text `consensus=exclude` and reason is not `FT_NOT_RETRIEVED` |
| Studies included in review | | database-arm studies after linking duplicate reports |
| Reports of included studies | | `included.tsv` rows that came from the deduplicated library |

## Other methods

These boxes are the second PRISMA 2020 arm. They are not title/abstract screening and they are not inside `records_after_deduplication`. Use 0 and say why when that route was not used.

| Box | n | Source of the number |
|-----|---|----------------------|
| Reports sought for retrieval | | Other-method records you tried to open |
| Reports not retrieved | | `FT_NOT_RETRIEVED` on this arm |
| Reports assessed for eligibility | | sought minus not retrieved |
| Reports excluded | | full-text exclusions on this arm, with reasons |
| Reports of included studies | | `included.tsv` rows that did not come from the deduplicated library |

`included.tsv` is one row per report from both arms. Do not count the same report in both included lines.

## Full-text exclusion reasons

| reason_code | n |
|-------------|---|
| FT_WRONG_DESIGN | |
| FT_NO_OUTCOME | |
| FT_DUPLICATE_REPORT | |
| FT_OTHER | |

The reason rows sum to the databases-and-registers "Reports excluded" box. `FT_NOT_RETRIEVED` is not in this table. If the other-methods arm excludes any report, list those reasons under that arm.

## Checks

```text
screened = title_abstract_excluded + reports_sought
reports_sought = not_retrieved + full_text_assessed
full_text_assessed = full_text_excluded + included_reports
```

The three lines are the databases-and-registers arm. `screened` starts from `records_after_deduplication`. `included_reports` in the third line is that arm only. Rows in `included.tsv` equal that number plus the other-methods included reports.

If "studies" is less than "reports", list which report ids belong to the same study. Do not merge them silently in the tsv; the tsv is one row per report.
