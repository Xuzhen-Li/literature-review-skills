# Narrative core set

Use this file only when `project.yaml` `review_type` is `narrative`. Systematic, scoping, and umbrella reviews stay on the full eligibility screen in `SKILL.md` and do not call `scripts/narrative_core.py check`.

A narrative core is the set the user agrees to read. It is not a complete systematic review. Records left out are logged as not read. They are not eligibility exclusions, and they are not dropped to hit a fixed number.

## Rank suggestion

After `inclusion_lock`, run:

```bash
python3 <suite>/skills/literature-screening/scripts/narrative_core.py rank \
  --library <project>/02-records/library.csv \
  --question "<locked question>" \
  --out <project>/03-screening/narrative_rank.tsv
```

The score counts content tokens shared by the locked question and the title plus abstract. Every library row stays in the file. The rank is a reading aid. It is not a decision, and the command has no maximum-core option.

## User confirmation

Write `03-screening/core_decision.tsv` with the user, not from the rank alone. Header: `record_id,decision`. `decision` is `core` or `not_read`. Every `library.csv` record appears once. The user chooses the size. Do not invent a cap, and do not add a `max_core` column.

Then:

- `03-screening/included.tsv` lists only the `core` rows, with the same columns as the full-screen included file.
- `03-screening/not_read.tsv` lists the other record ids. Header: `record_id`.
- `03-screening/screening.csv` has one `title_abstract` row per library record. Core rows use `decision` `include`, `reason_code` `CORE`, and `consensus` `include`. The rest use `decision` `not_read`, `reason_code` `NOT_READ`, and `consensus` `not_read`. Do not use `exclude` or `maybe`. Do not add a `full_text` stage for a not-read row.
- `03-screening/prisma_flow.md` is the short note below, not the systematic box table. Do not claim the PRISMA identification-to-inclusion equalities for this mode.

```text
# Narrative core note

This file is not a complete systematic review.
Records marked not read were outside the user-confirmed core and were not read.
They are not eligibility exclusions.

Core records: <N>
Not read: <M>
```

Check:

```bash
python3 <suite>/skills/literature-screening/scripts/narrative_core.py check \
  --library <project>/02-records/library.csv \
  --decisions <project>/03-screening/core_decision.tsv \
  --included <project>/03-screening/included.tsv \
  --not-read <project>/03-screening/not_read.tsv \
  --flow <project>/03-screening/prisma_flow.md \
  --screening <project>/03-screening/screening.csv \
  --review-type narrative
```

The command must print `OK narrative core`. Append `YYYY-MM-DD | literature-screening | narrative core confirmed, read <N>, not read <M> | human` only after the user agrees to that split.

Included records still go to `zotero-library-sync`. Not-read records do not get deep-reading notes.
