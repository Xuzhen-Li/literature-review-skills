---
name: review-orchestrator
description: >
  Reports the current literature-review stage from project.yaml and LOG.md,
  routes to exactly one next skill, and blocks advancement past an unpassed
  human gate. Trigger on "continue the review", "what is the next step",
  "where are we in the review", or "start the review workflow". Do not use
  it to draft prose, invent references, build a search string, or screen
  records.
---

# Review orchestrator

## When to use

Use this skill at the start of a session and whenever the user asks what to do next. It does not perform the next skill's work in the same breath as the status report. After the report, follow only the routed skill's `SKILL.md`.

## Inputs (paths) / Preconditions

- `<project>/project.yaml` and `<project>/LOG.md` when they exist.
- Gate names and pass rules in the suite file `shared/gates.md` (suite root is two levels above this file after symlinks are resolved). The six keys are listed below so this skill still runs if `shared/` is not installed beside it.
- Output paths named in the routing table. Do not create those files here.

`<project>` is the review folder. If the user gives a path, use it. Else if `./project.yaml` exists, use `.`. Else route to `review-project-setup` and ask where to create the folder. Do not guess a path.

## Procedure (numbered steps)

1. Read `project.yaml`. A gate is passed only when its line is the YAML boolean `true` (`topic_lock: true`). Missing, `false`, `"true"`, or `yes` means not passed.
2. Read `LOG.md` from the bottom. Do not treat an agent line as a user confirmation. Gate lines end with `| human`.
3. Walk routing rows 1 through 17 in order. Row 0 is this skill and is never the destination. The first row whose condition is true is the next skill. Later files do not cancel an earlier failed gate: if `09-draft/` has prose but `topic_lock` is not true, route back to `review-scoping-and-gaps`.
4. Print the status report (template below) and stop. Name the skill and the first action from that skill. Do not start a second skill in this turn.
5. If the user then confirms a gate in this chat, record it only when every file named for that gate in `shared/gates.md` already exists and the reply is a direct yes to the gate question. Set the boolean, append one log line, and route again. Otherwise leave the boolean false.

Status report:

```text
Project: <title or path>
Review type: <narrative|systematic|scoping|umbrella|unknown>
Passed gates: <list or none>
Current stage: <skill name>
Next skill: <skill name>
Why: <one sentence naming the missing file or the unpassed gate>
Also due: <figure-permissions if the ledger has adapted/reused rows still needed, else none>
Do not skip to: <the skill after next>
```

## Routing

| # | Skill | Enter when |
|---|-------|------------|
| 0 | `review-orchestrator` | Never selected. It only runs this table. |
| 1 | `review-project-setup` | `project.yaml` is missing or has no `review_type`. |
| 2 | `review-scoping-and-gaps` | `topic_lock` is not true. |
| 3 | `search-strategy-builder` | `topic_lock` is true and `search_lock` is not true. |
| 4 | `search-export-and-dedup` | `search_lock` is true and `02-records/library.csv` or `02-records/prisma_counts.json` is missing. |
| 5 | `literature-screening` | The library exists and (`inclusion_lock` is not true, or `03-screening/screening.csv`, `03-screening/prisma_flow.md`, or `03-screening/included.tsv` is missing). When `review_type` is `narrative`, also enter while `03-screening/core_decision.tsv` or `03-screening/not_read.tsv` is missing. |
| 6 | `zotero-library-sync` | `inclusion_lock` is true, `included.tsv` exists, and (`04-library/pdf_status.csv` is missing or lacks a row for any included `record_id`, or `04-library/collection_checklist.tsv` is missing, or any `user_confirmed` cell is not `yes`). |
| 7 | `paper-deep-reading` | Some included `record_id` has neither a `05-reading/*.md` file containing that id nor a `LOG.md` line that records a no-PDF skip for that id. |
| 8 | `exemplar-review-analysis` | Every included record has a note and `06-exemplars/style_brief.md` is missing. |
| 9 | `review-outline-builder` | The style brief exists and (`outline_lock` is not true, including when `07-outline/outline.md` is still `Status: draft`, or `review_type` is `systematic` and `07-outline/systematic_methods_checklist.md` is missing). |
| 10 | `review-figures-and-tables` | `outline_lock` is true and (`08-figures/figure_plan.md` or `08-figures/figure_ledger.csv` is missing, or an `original` ledger row has no SVG and PDF). `Fig. 1` uses `08-figures/fig-1.svg` and `fig-1.pdf`. `Table 1` uses `table-1`. `Box 1` uses `box-1`. A panel letter stays on the slug (`Fig. 2a` is `fig-2a`). |
| 11 | `review-section-drafter` | The figure files exist and any non-structural `## S<n>` section in the outline lacks `09-draft/S<nn>-*.md` containing `Status: checked`. Structural titles start with Acknowledgements, Acknowledgments, Funding, or Author contributions. Limitations and Next questions are required sections, not structural. |
| 12 | `journal-selection` | Every required section file is checked and `journal_lock` is not true. |
| 13 | `exemplar-review-analysis` | `journal_lock` is true and `06-exemplars/style_brief.md` does not contain both `Refreshed after journal lock: yes` and the recommended journal name. |
| 14 | `manuscript-polishing` | `journal_lock` is true, the style brief has that refresh line for the recommended journal, and `10-polish/manuscript_polished.docx` is missing. |
| 15 | `figure-permissions` | `10-polish/manuscript_polished.docx` exists and `figure_ledger.csv` has an `adapted` or `reused` row whose `permission_status` is not `granted` or `not_required`. Before that file exists, keep walking and list this skill under "Also due". |
| 16 | `submission-package` | The polished manuscript exists, open permission rows are cleared or the ledger has no `adapted`/`reused` rows, and `13-submission/` is empty or `final_submit` is not true. |
| 17 | `reviewer-response` | The user supplies a decision letter, or `14-revision/decision_letter.md`, `.txt`, or `.pdf` exists, and `14-revision/response_to_reviewers.docx` is missing or the user says a new letter arrived. |

An optional post-export cluster pass is not a row. After `02-records/library.csv` exists, the user may ask `review-scoping-and-gaps` to write `00-scope/export_clusters.md`. That pass may ask to reopen `topic_lock`. It does not run unless the user asks, and it does not replace the question-first scope report. Note export into the user's library is also not a row. It runs only after the user asks `zotero-library-sync`.

After `final_submit: true` with no decision letter, the report is: waiting for the journal. Do not invent a decision. The user submits the package. This skill never uploads it.

## Human gate(s)

Enforce these six. Do not add others. Questions and required files are in `shared/gates.md`.

| Key | Owner |
|-----|--------|
| `topic_lock` | `review-scoping-and-gaps` |
| `search_lock` | `search-strategy-builder` |
| `inclusion_lock` | `literature-screening` |
| `outline_lock` | `review-outline-builder` |
| `journal_lock` | `journal-selection` |
| `final_submit` | `submission-package` |

A checker script printing OK is not a gate. Only a direct user yes, written to `project.yaml` and `LOG.md`, passes a gate.

## Outputs (exact paths + formats)

The status report is the reply to the user. Do not write a second status file. The only edits this skill may make are a gate boolean the user just accepted and one appended `LOG.md` line:

```text
YYYY-MM-DD | review-orchestrator | <gate key> passed: <short quote of the user yes> | human
```

## Quality checklist

- The next skill is the first matching row from row 1 downward, not the skill the user finds most interesting.
- An unpassed earlier gate beats a later file that already exists.
- The report names a path that is missing or a gate that is false.
- No DOI, count, or journal metric was added to the report from memory.

## Guardrails

- Do not fabricate records, hit counts, or reviewer comments.
- Do not mark a gate true because the draft "looks ready".
- Do not delete `LOG.md` lines or other keys in `project.yaml`.
- Do not run database logins, payments, copyright transfer, or the journal Submit button.

## Next step

The single skill named in the status report.
