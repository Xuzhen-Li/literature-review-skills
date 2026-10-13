---
name: literature-screening
description: >
  Locks inclusion and exclusion criteria, then screens titles and abstracts
  and full texts with reasons, optional Cohen's kappa, and a PRISMA 2020
  flow that reconciles to the deduplicated library. Narrative reviews
  instead rank the library and keep the cap in project.yaml, logging the
  rest as not read. Trigger on "screen the papers", "inclusion criteria",
  "PRISMA flow", "kappa", or "narrative core". Do not use it to
  deduplicate, to fetch PDFs from shadow libraries, or to write the review.
---

# Literature screening

## Opening

On first use in a project, say this verbatim:

I am literature screening. I lock the criteria before any final decision, and a narrative review keeps the cap written in project.yaml.

## When to use

`02-records/library.csv` and `02-records/prisma_counts.json` exist. Criteria are drafted and locked here before any final exclude decision. Read `review_type` before choosing a path.

Narrative reviews do not claim a complete systematic flow. They lock criteria, then follow `references/narrative_core.md`: rank every record and keep `narrative_core_cap` from `project.yaml` (default 500). Ties at the cutoff stay in the core. The rest are `not_read` with reason `below-cap`. The agent does not change the cap. Systematic, scoping, and umbrella reviews use the numbered steps below and do not write a narrative core.

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

3. Ask: "Pass inclusion lock on 03-screening/criteria.md? Reply with: I confirm the inclusion lock." On that exact sentence, set `gates.inclusion_lock` to `true` and append `YYYY-MM-DD | literature-screening | inclusion lock passed | human`. Check the sentence with `skills/review-orchestrator/scripts/check_gate_phrase.py --gate inclusion_lock`. Do not write final screening rows before it matches.

If `review_type` is `narrative`, stop this numbered procedure here and follow `references/narrative_core.md`. Do not run steps 4–9. Systematic, scoping, and umbrella reviews continue at step 4. They do not write `narrative_rank.tsv`, `core_decision.tsv`, or `not_read.tsv`, and they do not call `scripts/narrative_core.py`.

4. Title and abstract: one row per record per screener in `03-screening/screening.csv`. Columns: `record_id,stage,screener,decision,reason_code,reason_note,date,consensus`. `stage` is `title_abstract`. `decision` is `include`, `exclude`, or `maybe`. `exclude` requires a `reason_code`. Single screener: `consensus` equals `decision`. Two screeners: `consensus` stays empty until they resolve disagreements; then it is `include` or `exclude`.
5. (Optional) To use ASReview LAB (an active learning screening tool) for title and abstract screening, open macOS Terminal or Windows PowerShell and run this from the suite root (the folder that contains `skills/`) to export the library:

```bash
python3 skills/literature-screening/scripts/asreview_io.py export <project>/02-records/library.csv -o <project>/03-screening/asreview_input.csv
```

Import `asreview_input.csv` (a CSV/TSV spreadsheet file) into an ASReview LAB browser window. When finished, download the exported results and convert them back to a staging file (a temporary file before final screening):

```bash
python3 skills/literature-screening/scripts/asreview_io.py import <asreview_export.csv> -o <project>/03-screening/asreview_decisions.csv
```

Manually add a `reason_code` for excludes, set `consensus`, and copy the rows into `screening.csv`. The `asreview_io.py` script counts unlabelled records as `not_seen` and writes no rows for them in `screening.csv`. They are still unscreened, not excluded, so the PRISMA numbers will not balance until they are screened. The stopping rule used in ASReview must be reported.

6. Full text: for every record with title/abstract `consensus` of `include` or `maybe`, add `stage` `full_text`. Retrieval failure is not an eligibility exclusion. Those records are "reports not retrieved" in the flow, with `reason_code` `FT_NOT_RETRIEVED`, and they do not go in the excluded-by-reason list.
7. Build `03-screening/included.tsv` for records whose full-text `consensus` is `include`. Header: `record_id,doi,pmid,title,year,first_author,n_authors,venue,citation_key`. Copy identifiers from `library.csv`. Put the `journal` value in `venue`. `citation_key` is the first author's family name (ASCII letters) plus the four-digit year (`Lovelace2020`). Collisions get a trailing `a`, `b`, or `c`. `n_authors` is the count of authors joined by `; ` (semicolon then space), or empty if the author field is empty. RIS and NBIB rows already use that separator. If a CSV cell uses another separator, rewrite that cell to `; ` before counting. Do not invent a missing author.
8. Write `03-screening/prisma_flow.md` from `references/prisma_flow_template.md`. These equalities are the databases-and-registers arm. Use `records_after_deduplication` as the screened denominator unless you list extra removals (automation or other) with counts:

```text
screened = title_abstract_excluded + reports_sought
reports_sought = not_retrieved + full_text_assessed
full_text_assessed = full_text_excluded + included_reports
sum of full-text reason counts = full_text_excluded
```

`full_text_excluded` does not include `FT_NOT_RETRIEVED`. If the sums fail, fix the CSV. Do not edit the flow numbers alone.

   Optional diagram: write `03-screening/prisma_counts_flow.json` (keys in `references/prisma_flow_examples/counts_example.json`) and run:

```bash
python3 <suite>/skills/literature-screening/scripts/prisma_flow.py \
  <project>/03-screening/prisma_counts_flow.json \
  --out <project>/03-screening/prisma_flow
```

   This optional diagram step is for systematic, scoping, or umbrella reviews that need figure files. Run it after the `03-screening/prisma_flow.md` numbers reconcile. The keys in `03-screening/prisma_counts_flow.json` match the example file, and the script checks that the screened, sought, assessed, and included numbers follow the same math rules as `03-screening/prisma_flow.md`. The script creates `03-screening/prisma_flow.svg` and `03-screening/prisma_flow.pdf`, but it does not replace the `03-screening/prisma_flow.md` text document.

9. Append `YYYY-MM-DD | literature-screening | screening complete, included <N> | agent` with N equal to the included-report count.

## Human gate(s)

`inclusion_lock` before any final row in `screening.csv` or `core_decision.tsv`. A kappa number does not lock the criteria. The user does. An optional decision card may come first (`shared/decision_cards.md`): four labeled options, one preferred, and a custom option rewritten as a plan with its risks. The card is not the lock. Only the exact sentence is.

## Outputs (exact paths + formats)

- `03-screening/criteria.md`
- `03-screening/pilot.csv` and `kappa.json` when a dual pilot was run
- `03-screening/screening.csv` — columns in step 4, or the narrative columns in `references/narrative_core.md`
- `03-screening/included.tsv` — columns in step 7
- `03-screening/prisma_flow.svg` and `prisma_flow.pdf` when the optional diagram was drawn
- `03-screening/prisma_flow.md` — PRISMA 2020 boxes for a full eligibility screen, or the narrative core note
- Narrative only: `03-screening/narrative_rank.tsv`, `core_decision.tsv`, `not_read.tsv`, and `cap_overflow.tsv`

## Quality checklist

- No `screening.csv` row has a date earlier than the inclusion-lock log line.
- Every `exclude` has a reason code defined in `criteria.md`.
- Flow arithmetic matches `prisma_counts.json` and the CSV.
- Included DOIs and PMIDs match `library.csv` for that `record_id`.
- Single-screener reviews have a `single_screener` log line and no fabricated kappa file.
- A narrative project prints `OK narrative core`, says it is not a complete systematic review, and logs every non-core record as not read.

## Guardrails

- Do not exclude a record for "low quality" unless a reason code says so and was locked.
- Do not drop duplicates again here. Duplicates were removed in `02-records/`.
- Do not download a PDF from an unauthorized site to decide full text. If you cannot retrieve it legally, count it as not retrieved.
- Maybe at title/abstract goes to full text. It is not a silent exclude.
- Do not change `narrative_core_cap`, and do not describe that core as a systematic review. Do not use the cap for a systematic, scoping, or umbrella review.

## Next step

`zotero-library-sync` using `included.tsv`.
