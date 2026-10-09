# Human gates

A gate passes only when `project.yaml` contains the YAML boolean `true` for that key and `LOG.md` has a new line recording the user's confirmation. The agent may write the line. The agent may not confirm the gate.

Log line (append only, no table):

```text
YYYY-MM-DD | <skill-name> | <decision> | human
```

Use `| agent` only for a mechanical note such as a file being written. A gate line always ends with `| human`. Do not delete earlier lines.

Passed line (example). The key stays under `gates`, as in `project.yaml`:

```yaml
gates:
  topic_lock: true
```

`false`, `"true"`, `yes`, or a missing key means not passed.

The six gates are `topic_lock`, `search_lock`, `inclusion_lock`, `outline_lock`, `journal_lock`, and `final_submit`. Checkpoints below are recorded in `LOG.md` but are not extra gates.

Installed skill folders do not include this file. Each owning skill repeats its own pass condition.

## topic_lock

- Owner: `review-scoping-and-gaps`
- Ask: "Pass topic lock on angle [letter and title]? Reply yes or no."
- Files that must already exist: `00-scope/scope_report.md`
- On yes: set `gates.topic_lock` to `true`, set `updated`, append `LOG.md`
- Blocks: `search-strategy-builder` and every later skill

## search_lock

- Owner: `search-strategy-builder`
- Ask: "Pass search lock on the strings in 01-search/search_strings.md dated [date]? Reply yes or no."
- Files: `01-search/search_strings.md`, `01-search/hit_counts.tsv`
- Condition: every searched database has a user-pasted hit count and a search date. Cells still marked `[VERIFY]` block the gate.
- On yes: set `gates.search_lock` to `true`
- Blocks: `search-export-and-dedup` and every later skill

## inclusion_lock

- Owner: `literature-screening`
- Ask: "Pass inclusion lock on 03-screening/criteria.md? Reply yes or no."
- Files: `03-screening/criteria.md`
- Condition: the pilot, if run, is finished and the criteria text the user is locking is the post-pilot text. Provisional pilot decisions are not final exclusions.
- On yes: set `gates.inclusion_lock` to `true`
- Blocks: final rows in `03-screening/screening.csv` and every later skill

## outline_lock

- Owner: `review-outline-builder`
- Ask: "Pass outline lock on 07-outline/outline.md? Reply yes or no."
- Files: `07-outline/outline.md`
- Condition: each section has a claim, the evidence ids that can support it, planned figures or tables, and a word budget.
- On yes: set `gates.outline_lock` to `true`
- Blocks: `review-section-drafter` and every later skill

## journal_lock

- Owner: `journal-selection`
- Ask: "Pass journal lock on [journal name], checked on [date] at [official URL]? Reply yes or no."
- Files: `11-journal/journal_shortlist.md`
- Condition: scope, article type, invitation requirement, APC, and word limits were read on the journal's site on the stated date. Figures remembered from memory do not count.
- On yes: set `gates.journal_lock` to `true`
- Blocks: `manuscript-polishing` and submission

## final_submit

- Owner: `submission-package`
- Ask: "The package in 13-submission/ is ready for you to submit. Pass final submit readiness? Reply yes or no. The agent will not submit."
- Files: at least one file in `13-submission/`, plus `10-polish/manuscript_polished.docx`
- Condition: reused or adapted figures are cleared in `12-permissions/permissions_log.csv`, or the ledger shows no reused or adapted items. The user uploads and submits.
- On yes: set `gates.final_submit` to `true`
- Blocks: nothing further except waiting for a decision letter. Passing the gate does not submit the manuscript.

## Checkpoints (not gates)

Record these in `LOG.md` when they happen.

| Token | Meaning |
|-------|---------|
| `project_confirmed` | User confirmed `project.yaml` after setup |
| `exports_complete` | User confirmed the raw exports in `02-records/raw/` are the full searches |
| `draft_complete` | User confirmed every outlined section has a file in `09-draft/` |
| `single_screener` | Only one person screened. Kappa was not invented |

## Routing files

`review-orchestrator` uses these paths. Do not rename them.

| Signal | Path |
|--------|------|
| Project | `project.yaml`, `LOG.md` |
| Scope | `00-scope/scope_report.md` |
| Search | `01-search/search_strings.md`, `01-search/hit_counts.tsv` |
| Library | `02-records/library.csv`, `02-records/prisma_counts.json` |
| Screening | `03-screening/criteria.md`, `03-screening/screening.csv`, `03-screening/prisma_flow.md` |
| Included set | `03-screening/included.tsv` |
| PDFs | `04-library/pdf_status.csv` |
| Notes | `05-reading/<citation_key>.md` |
| Evidence | `evidence/evidence_table.csv` |
| Exemplars | `06-exemplars/style_brief.md` |
| Outline | `07-outline/outline.md` |
| Figures | `08-figures/figure_plan.md`, `08-figures/figure_ledger.csv` |
| Draft | `09-draft/*.md` |
| Polish | `10-polish/manuscript_polished.docx` |
| Journal | `11-journal/journal_shortlist.md` |
| Permissions | `12-permissions/permissions_log.csv` |
| Submission | `13-submission/` |
| Revision | `14-revision/response_to_reviewers.docx` |

A decision letter may be saved as `14-revision/decision_letter.md`, `.txt`, or `.pdf`.
