---
name: literature-screening
description: >
  Locks inclusion and exclusion criteria, then screens titles and abstracts
  and full texts with reasons, optional Cohen's kappa, and a PRISMA 2020
  flow that reconciles to the deduplicated library. Trigger on "screen the
  papers", "inclusion criteria", "PRISMA flow", or "kappa". Do not use it
  to deduplicate, to fetch PDFs from shadow libraries, or to write the review.
---

# Literature screening

## When to use

`02-records/library.csv` and `02-records/prisma_counts.json` exist. Criteria are drafted and locked here before any final exclude decision.

## Inputs (paths) / Preconditions

- `<project>/02-records/library.csv` and `prisma_counts.json`.
- `<project>/00-scope/scope_report.md` — locked question and framework.
- `references/criteria_template.md` and `references/prisma_flow_template.md`.
- Optional second screener. If there is only one, do not invent kappa. Log `single_screener`.
- `scripts/kappa.py` for a pilot CSV with two decision columns.

PRISMA 2020 flow labels: https://www.prisma-statement.org/

## Procedure (numbered steps)

1. Copy `references/criteria_template.md` to `03-screening/criteria.md`. Fill include and exclude rules from the locked framework. Each rule gets a `reason_code` from the template. Add a rule only when the user wants it. A language or date rule must repeat the justification already used in the search file.
2. Optional pilot, before the lock: take the first 20 to 30 rows of `library.csv` (or a user-specified random subset; record the seed if you sample). Two people decide `include` or `exclude` independently. Write `03-screening/pilot.csv` with `record_id,screener_a,screener_b`. Run:

```bash
python3 <suite>/skills/literature-screening/scripts/kappa.py \
  --csv <project>/03-screening/pilot.csv \
  --a screener_a --b screener_b \
  --out <project>/03-screening/kappa.json
```

`<suite>` is the directory that contains `skills/`. Bands in the JSON `interpretation` field follow Landis and Koch (Biometrics, 1977): `poor`, `slight`, `fair`, `moderate`, `substantial`, `almost_perfect`. If kappa is below 0.60, or the JSON says `undefined` because expected agreement is 1, revise the criteria wording and repeat the pilot. Pilot decisions are provisional. They are not copied into `screening.csv`.

3. Ask: "Pass inclusion lock on 03-screening/criteria.md? Reply yes or no." On yes, set `gates.inclusion_lock` to `true` and append `YYYY-MM-DD | literature-screening | inclusion lock passed | human`. Do not write final screening rows before this yes.
4. Title and abstract: one row per record per screener in `03-screening/screening.csv`. Columns: `record_id,stage,screener,decision,reason_code,reason_note,date,consensus`. `stage` is `title_abstract`. `decision` is `include`, `exclude`, or `maybe`. `exclude` requires a `reason_code`. Single screener: `consensus` equals `decision`. Two screeners: `consensus` stays empty until they resolve disagreements; then it is `include` or `exclude`.
5. Full text: for every record with title/abstract `consensus` of `include` or `maybe`, add `stage` `full_text`. Retrieval failure is not an eligibility exclusion. Those records are "reports not retrieved" in the flow, with `reason_code` `FT_NOT_RETRIEVED`, and they do not go in the excluded-by-reason list.
6. Build `03-screening/included.tsv` for records whose full-text `consensus` is `include`. Header: `record_id,doi,pmid,title,year,first_author,n_authors,venue,citation_key`. Copy identifiers from `library.csv`. Put the `journal` value in `venue`. `citation_key` is the first author's family name (ASCII letters) plus the four-digit year (`Lovelace2020`). Collisions get a trailing `a`, `b`, or `c`. `n_authors` is the count of authors joined by `; ` (semicolon then space), or empty if the author field is empty. RIS and NBIB rows already use that separator. If a CSV cell uses another separator, rewrite that cell to `; ` before counting. Do not invent a missing author.
7. Write `03-screening/prisma_flow.md` from `references/prisma_flow_template.md`. These equalities are the databases-and-registers arm. Use `records_after_deduplication` as the screened denominator unless you list extra removals (automation or other) with counts:

```text
screened = title_abstract_excluded + reports_sought
reports_sought = not_retrieved + full_text_assessed
full_text_assessed = full_text_excluded + included_reports
sum of full-text reason counts = full_text_excluded
```

`full_text_excluded` does not include `FT_NOT_RETRIEVED`. If the sums fail, fix the CSV. Do not edit the flow numbers alone.

8. Append `YYYY-MM-DD | literature-screening | screening complete, included <N> | agent` with N equal to the included-report count.

## Human gate(s)

`inclusion_lock` before any final row in `screening.csv`. A kappa number does not lock the criteria. The user does.

## Outputs (exact paths + formats)

- `03-screening/criteria.md`
- `03-screening/pilot.csv` and `kappa.json` when a dual pilot was run
- `03-screening/screening.csv` — columns in step 4
- `03-screening/included.tsv` — columns in step 6
- `03-screening/prisma_flow.md` — PRISMA 2020 boxes, both database and other-source arms

## Quality checklist

- No `screening.csv` row has a date earlier than the inclusion-lock log line.
- Every `exclude` has a reason code defined in `criteria.md`.
- Flow arithmetic matches `prisma_counts.json` and the CSV.
- Included DOIs and PMIDs match `library.csv` for that `record_id`.
- Single-screener reviews have a `single_screener` log line and no fabricated kappa file.

## Guardrails

- Do not exclude a record for "low quality" unless a reason code says so and was locked.
- Do not drop duplicates again here. Duplicates were removed in `02-records/`.
- Do not download a PDF from an unauthorized site to decide full text. If you cannot retrieve it legally, count it as not retrieved.
- Maybe at title/abstract goes to full text. It is not a silent exclude.

## Next step

`zotero-library-sync` using `included.tsv`.
