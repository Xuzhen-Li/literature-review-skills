# literature-review-skills — Design Spec (clean-room)

Author: Xuzhen Li. License: MIT.

This suite is an original work. It is written from public, citable norms only
(PRISMA 2020, PRISMA-S, Cochrane Handbook ch. 4, JBI scoping-review guidance,
ICMJE recommendations, COPE guidance, publisher author guidelines, Zotero /
PubMed / Web of Science / Scopus official docs, Unpaywall, Crossref, RightsLink).
No third-party commercial skill pack text may be consulted or reproduced.

## Goal

An agent-agnostic skill suite (Cursor, Claude Code, Codex — any tool that reads
`SKILL.md`) that takes a researcher from a vague topic to a submitted review
article and through peer-review revision, with every claim traceable to a
source and no fabricated references.

Language: **English only** (instructions, templates, file names, outputs).

## Core principles (apply to every skill)

1. Evidence first: every factual sentence in a draft must map to a record in
   `evidence/evidence_table.csv` (or be marked `[NEEDS SOURCE]`).
2. Never fabricate DOIs, PMIDs, authors, years, journals, data, or reviewer
   responses. Unknown → `[VERIFY]`.
3. Human gates: the agent stops and asks for one exact sentence at defined
   gates (institutional access, topic lock, search string lock, inclusion
   criteria lock, outline lock, journal lock, final submit). The homepage
   is opened before the rest of the project file. Gates are listed in each
   skill. `yes` does not pass.
4. Credentials and legal acts (logins, payments, copyright transfer, final
   Submit) are always performed by the user. The agent never types or stores
   a password. If the computer cannot download a paper, it gives the DOI
   and the user uploads the PDF.
5. Dynamic facts (impact factor, APC, word limits, journal scope) must be
   checked live on the official journal site and dated.
6. Copyright-safe figures: default to original schematics and synthesis
   tables, written as editable SVG plus PDF. A published panel may be
   cropped only from a local PDF, with source, page, crop box, and
   copyright status in `panel_crop_ledger.csv`. `needs-permission` is not
   publication-ready. Any other reuse is logged and routed to permissions.
7. One project folder, predictable layout (below). Each skill reads its
   inputs from earlier folders and writes only to its own folder.
8. An exact sentence is the only gate record. An optional four-option
   decision card may precede it and does not replace it. Each skill says
   one fixed introduction on first use (`shared/skill_intro.md`).

## Project layout (created by `review-project-setup`)

```
<project>/
  project.yaml            # topic, review type, audience, target journal, gates passed
  00-scope/
  01-search/
  02-records/             # raw exports, deduplicated library, PRISMA counts
  03-screening/
  04-library/             # Zotero collection map, PDF status
  05-reading/             # per-paper notes
  evidence/evidence_table.csv
  06-exemplars/
  07-outline/
  08-figures/
  09-draft/
  10-polish/
  11-journal/
  12-permissions/
  13-submission/
  14-revision/
  LOG.md                  # append-only decision log (date, skill, decision, by whom)
```

## Skills (18)

Directory name = skill `name` (kebab-case). Each lives in `skills/<name>/`.

| # | name | Purpose | Key outputs |
|---|------|---------|-------------|
| 0 | `review-orchestrator` | Entry point. Reads `project.yaml` + `LOG.md`, reports current stage, routes to the next skill, enforces gates. | status report |
| 1 | `review-project-setup` | Open the database homepage first, then create the layout, interview the user, and write `project.yaml` with `narrative_core_cap`. | `project.yaml`, `LOG.md` |
| 2 | `review-scoping-and-gaps` | Quick landscape scan, candidate angles, gap statements, feasibility (record counts), recommend one angle; gate: topic lock. Optional later clustering of the exported library may ask to reopen that lock. It does not replace the question-first order. | `00-scope/scope_report.md` |
| 3 | `search-strategy-builder` | PICO/PEO/SPIDER concepts → synonyms, MeSH/Emtree, field tags; per-database strings (PubMed, WoS, Scopus); test-run counts; PRISMA-S reporting block; gate: search lock. Optional wide, middle, and tight strings when a pasted hit count is extreme; exactly one string is locked. | `01-search/search_strings.md` |
| 4 | `search-export-and-dedup` | Export searches. Agent browser first; if not logged in, computer control of the user's browser, with the user typing any password. Otherwise the user exports RIS/NBIB/CSV. Deduplicate by DOI → PMID → normalized title+year. Include a Python dedup script with tests. | `02-records/library.csv`, `prisma_counts.json` |
| 5 | `literature-screening` | Inclusion/exclusion criteria (gate), title/abstract then full-text screening with reasons, optional dual-screener agreement (Cohen's kappa), PRISMA 2020 flow numbers. Narrative reviews keep `narrative_core_cap` and log the rest as not read. | `03-screening/screening.csv`, `prisma_flow.md` |
| 6 | `zotero-library-sync` | Import included records to Zotero (RIS), collection map by theme, a checklist the user confirms, legal full-text retrieval. When download permission is missing, write a DOI list for the user to upload. Never use shadow libraries. | `04-library/pdf_status.csv`, `doi_for_upload.tsv` |
| 7 | `paper-deep-reading` | Per-paper structured note (question, design, key findings with page refs, limitations, quotable figure ideas), and append rows to evidence table. Short quotes only, with page numbers. | `05-reading/*.md`, evidence rows |
| 8 | `exemplar-review-analysis` | Pick 3-5 recent reviews the user can legally open; analyze structure, section length, figure count, citation density, tone; produce a style brief. After journal lock, refresh that brief from reviews in the locked journal. Do not rank them by an unopened metric. | `06-exemplars/style_brief.md` |
| 9 | `review-outline-builder` | Thematic synthesis → outline with section claims, evidence IDs per section, planned figures/tables, word budget, plus required limitations and next-questions sections; gate: outline lock. Systematic reviews also get a registration reminder and a bias-tool checklist. Pooled estimates stay out unless the user asks and the outline says so. | `07-outline/outline.md` |
| 10 | `review-figures-and-tables` | Plan Fig. 1 (original argument map), synthesis tables, timelines, comparison matrices; for each item record type (original / adapted / reused), sources, and permission status. Draw each original item as SVG plus PDF. Do not crop published figures. | `08-figures/figure_plan.md`, `figure_ledger.csv`, `fig-1.svg`, `fig-1.pdf` |
| 11 | `review-section-drafter` | Draft Introduction, body sections, limitations, next questions, and conclusions one section at a time from outline + evidence table; inline citation keys; claim-strength check (hedging matches evidence level). Refuse a finished draft while limitations or next questions are absent. | `09-draft/*.md` |
| 12 | `journal-selection` | Shortlist 3-5 journals (scope, article type accepts reviews, invited-only?, OA/APC, turnaround, indexing), verify live, recommend; gate: journal lock. A national partition or citation metric is copied only from an official page opened that day. No matcher sites. | `11-journal/journal_shortlist.md` |
| 13 | `manuscript-polishing` | Apply the refreshed style brief (heading pattern, abstract shape, figure budget), then journal-style adaptation, language edit, consistency, overclaim scan, citation-to-evidence audit. No new claims. | `10-polish/manuscript_polished.docx`, change log |
| 14 | `figure-permissions` | For each reused/adapted item: determine license (CC-BY etc.), RightsLink or publisher request, request email template, caption credit lines, risk list. | `12-permissions/permissions_log.csv` |
| 15 | `submission-package` | Cover letter as markdown and a word-processor file, a portal field guide quoted from the author page, title page, declarations (funding, COI, data, AI-use disclosure per journal), suggested reviewers (with conflict check), file checklist and upload order. Highlights, and a visual abstract as an original SVG plus PDF, only when the author page requires them. | `13-submission/` |
| 16 | `reviewer-response` | Parse decision letter, number every comment, plan actions, draft point-by-point response with exact change locations; never claim a change that was not made. | `14-revision/response_to_reviewers.docx` |
| on request | `review-writing` | Revise an existing review (markdown or docx): inventory, argument diagnosis and blueprint, mechanism/problem-chain restructure, claim-mechanism-evidence-boundary-synthesis paragraphs, template-prose removal, live Zotero fields, page-by-page render QC. Modes: language, structural, full-word. | revised manuscript, `*.orig.*` backup, change log, comment table, author-check list |

## Per-skill file contract

```
skills/<name>/
  SKILL.md          # required
  references/       # optional: checklists, templates, longer guidance
  scripts/          # optional: deterministic helpers (Python 3.9+, stdlib or pandas)
  tests/            # required if scripts/ exists (pytest)
```

`SKILL.md` structure (keep under ~250 lines; move long templates to references/):

```
---
name: <name>
description: <one paragraph: what it does + concrete trigger phrases + when NOT to use>
---
# <Title>
## When to use
## Inputs (paths) / Preconditions
## Procedure (numbered steps)
## Human gate(s)
## Outputs (exact paths + formats)
## Quality checklist
## Guardrails
## Next step
```

## Repo-level files

- `README.md` (what, who, install for Cursor/Claude Code/Codex, workflow diagram in Mermaid, quick start, skill table)
- `LICENSE` (MIT, Copyright (c) 2026 Xuzhen Li)
- `install.sh` (copies or symlinks `skills/*` into `~/.cursor/skills`, `~/.claude/skills`, or `~/.codex/skills`, chosen by flag, placing `shared/` inside each copied skill in copy mode; idempotent)
- `shared/` — `evidence_table_schema.md`, `gates.md`, `writing_rules.md`, `decision_cards.md`, `skill_intro.md`
- `CHANGELOG.md`
- `.github/` added later by the repo-decoration bot.

Version 0.2.0 adds the narrative core, original figure files, required limitations and next-questions sections, a post-lock style refresh that polishing must follow, and the optional passes named in the skill table above.

Version 0.3.0 adds the project cap for narrative reviews, logged crops of local PDFs, a homepage gate, exact gate sentences, a fixed introduction for each skill, and a DOI upload list when this computer cannot download a paper. Desktop control may open the user's own browser. It does not type a password or fetch a paywalled PDF.

## SKILL.md frontmatter check

Frontmatter is a hidden settings block at the top of a text file. The `scripts/check_skills.py` script validates portable `SKILL.md` frontmatter under a folder like `skills/` and requires it to start and end with `---` lines. The script requires a non empty `name` matching the parent folder, a `description` under 1024 characters, and a whole file count under 500 lines. A terminal is a text window where you can type commands directly to your computer. Type `python3 scripts/check_skills.py` in Terminal on macOS or PowerShell on Windows to run it on the default folder, which returns an exit code of 0 when clean or 1 when a problem is found.
