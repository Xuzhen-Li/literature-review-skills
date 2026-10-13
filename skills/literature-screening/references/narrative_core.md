# Narrative core set

Use this file only when `project.yaml` `review_type` is `narrative`. Systematic, scoping, and umbrella reviews stay on the full eligibility screen in `SKILL.md` and do not call `scripts/narrative_core.py`.

The core is the most relevant records up to `narrative_core_cap` in `project.yaml`. Setup writes `500`. The agent does not change that number. Records below the cap are not read. They are not eligibility exclusions. This file is not a complete systematic review.

## Rank and cap

After `inclusion_lock`, run:

```bash
python3 <suite>/skills/literature-screening/scripts/narrative_core.py apply \
  --library <project>/02-records/library.csv \
  --question "<locked question>" \
  --cap <narrative_core_cap> \
  --rank-out <project>/03-screening/narrative_rank.tsv \
  --decisions <project>/03-screening/core_decision.tsv \
  --not-read <project>/03-screening/not_read.tsv \
  --overflow <project>/03-screening/cap_overflow.tsv
```

Pass the integer already stored in `project.yaml`. Do not pass `--max-core`.

The score counts content tokens shared by the locked question and the title plus abstract. Every library row stays in the rank file. The first `narrative_core_cap` rows are the core. If the next rows share that cutoff score, they stay in the core and are listed in `cap_overflow.tsv` with reason `tie-at-cutoff`. Every lower row is `not_read` with reason `below-cap`. A library smaller than the cap is all core.

## Files

- `03-screening/core_decision.tsv` header: `record_id`, `decision`, `reason`. `decision` is `core` or `not_read`.
- `03-screening/included.tsv` lists only the core rows, with the same columns as the full-screen included file.
- `03-screening/not_read.tsv` lists the below-cap record ids. Header: `record_id`, `reason`.
- `03-screening/screening.csv` has one `title_abstract` row per library record. Core rows use `decision` `include`, `reason_code` `CORE`, and `consensus` `include`. The rest use `decision` `not_read`, `reason_code` `below-cap`, and `consensus` `not_read`. Do not use `exclude` or `maybe`.
- `03-screening/prisma_flow.md` is the short note below. Do not claim the PRISMA identification-to-inclusion equalities for this mode.

```text
# Narrative core note

This file is not a complete systematic review.
Records marked not read were below the narrative cap and were not read.
They are not eligibility exclusions.

Cap: <narrative_core_cap>
Core records: <N>
Kept by a tie at the cutoff: <T>
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
  --rank <project>/03-screening/narrative_rank.tsv \
  --overflow <project>/03-screening/cap_overflow.tsv \
  --cap <narrative_core_cap> \
  --review-type narrative
```

The command must print `OK narrative core`. Append `YYYY-MM-DD | literature-screening | narrative cap <N> applied, read <core>, not read <M> | agent` after the check. The user has already passed `inclusion_lock` with the exact sentence in `shared/gates.md`.

Included records still go to `zotero-library-sync`. Not-read records do not get deep-reading notes.
