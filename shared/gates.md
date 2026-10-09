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
- Condition: every searched database has a user-pasted hit count and a search date, and exactly one string marked `- Locked: yes`. Cells still marked `[VERIFY]` block the gate.
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
- Condition: each section has a claim, the evidence ids that can support it, planned figures or tables, and a word budget. Limitations and Next questions are separate sections. A systematic review also has `07-outline/systematic_methods_checklist.md`.
- On yes: set `gates.outline_lock` to `true`
- Blocks: `review-section-drafter` and every later skill

## journal_lock

- Owner: `journal-selection`
- Ask: "Pass journal lock on [journal name], checked on [date] at [official URL]? Reply yes or no."
- Files: `11-journal/journal_shortlist.md`
- Condition: scope, article type, invitation requirement, APC, and word limits were read on the journal's site on the stated date. A national partition or a citation metric is present only when that same file has a source line from an official page opened that day. Figures remembered from memory do not count.
- On yes: set `gates.journal_lock` to `true`. `exemplar-review-analysis` then refreshes the style brief before `manuscript-polishing`.
- Blocks: `manuscript-polishing` until that refresh is in the brief, and submission

## final_submit

- Owner: `submission-package`
- Ask: "The package in 13-submission/ is ready for you to submit. Pass final submit readiness? Reply yes or no. The agent will not submit."
- Files: at least one file in `13-submission/`, `13-submission/cover_letter.docx`, `13-submission/portal_field_guide.md`, plus `10-polish/manuscript_polished.docx`. When `file_checklist.md` says `Highlights: required`, `highlights.md` exists. When it says `Visual abstract: required`, `visual_abstract.md`, `visual_abstract.svg`, and `visual_abstract.pdf` exist. When a line says `not required`, that item is not drafted.
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
| `narrative_core_confirmed` | The user confirmed which narrative records will be read. The rest stay not read |
| `collection_checklist_confirmed` | The user confirmed the Zotero collection list against the theme list |
| `style_brief_refreshed` | The style brief was rewritten from lawful reviews in the locked journal |
| `notes_attached` | The user asked for note export and the attachment log was updated |

## Optional decision cards

Before any of the six yes or no questions, the owning skill may show a decision card. The card has four labeled options, one marked preferred. A custom option is rewritten as a concrete plan with its risks. The card is not a gate and it does not change `project.yaml`. The lock is still a direct yes. The shape is in `shared/decision_cards.md`.

## Routing files

`review-orchestrator` uses these paths. Do not rename them.

| Signal | Path |
|--------|------|
| Project | `project.yaml`, `LOG.md` |
| Scope | `00-scope/scope_report.md` (optional later file: `00-scope/export_clusters.md`) |
| Search | `01-search/search_strings.md`, `01-search/hit_counts.tsv` |
| Library | `02-records/library.csv`, `02-records/prisma_counts.json` |
| Screening | `03-screening/criteria.md`, `03-screening/screening.csv`, `03-screening/prisma_flow.md` |
| Narrative core | `03-screening/narrative_rank.tsv`, `03-screening/core_decision.tsv`, `03-screening/not_read.tsv` |
| Included set | `03-screening/included.tsv` |
| PDFs | `04-library/pdf_status.csv` |
| Collections | `04-library/collection_checklist.tsv` |
| Note export | `04-library/note_attachment_log.tsv` (only after the user asks) |
| Notes | `05-reading/<citation_key>.md` |
| Evidence | `evidence/evidence_table.csv` |
| Exemplars | `06-exemplars/style_brief.md` |
| Outline | `07-outline/outline.md` |
| Systematic checklist | `07-outline/systematic_methods_checklist.md` |
| Figures | `08-figures/figure_plan.md`, `08-figures/figure_ledger.csv`, and `08-figures/<slug>.svg` plus `.pdf` for each original item |
| Draft | `09-draft/*.md` |
| Polish | `10-polish/manuscript_polished.docx` |
| Journal | `11-journal/journal_shortlist.md` |
| Permissions | `12-permissions/permissions_log.csv` |
| Submission | `13-submission/`, including `cover_letter.docx` and `portal_field_guide.md`. `highlights.md` when required. `visual_abstract.md`, `visual_abstract.svg`, and `visual_abstract.pdf` when a visual abstract is required |
| Revision | `14-revision/response_to_reviewers.docx` |

A decision letter may be saved as `14-revision/decision_letter.md`, `.txt`, or `.pdf`.
