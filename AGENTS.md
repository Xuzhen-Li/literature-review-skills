# AGENTS.md

AGENTS.md is a guidance file for Codex and other agents. This repository provides 18 literature-review skills (stage instruction packs), `shared/` rules, and `install.sh`. To install skills into `~/.cursor/skills`, `~/.claude/skills`, or `~/.agents/skills` (which Codex reads), run `install.sh` with `--target` set to `cursor`, `claude`, `agents`, or `all` (default `all`). This file helps humans and agents locate skill paths, gates (checkpoints), and tests.

## Start here

Pick the entry skill from what the user already has (full table: `docs/START_HERE.md`): topic only -> `review-project-setup`; own papers/DOI list -> `review-project-setup` then `search-export-and-dedup` (`--source manual`); a draft -> `review-writing` (no `project.yaml` needed); near-final manuscript -> `journal-selection`; decision letter -> `reviewer-response`; unsure -> `review-orchestrator`. No library account: gate sentence `I will use open-access sources only`, then `skills/zotero-library-sync/scripts/find_oa_pdfs.py` for legal free PDFs. Never use shadow libraries.

## Repository layout

- `skills/<name>/SKILL.md`
- `skills/<name>/references/`
- `skills/<name>/scripts/`
- `skills/<name>/tests/`
- `shared/`
- `install.sh`
- `docs/DESIGN.md`

## Skills

Below are the 18 skills provided by this repository:

| Skill | Path |
|---|---|
| `exemplar-review-analysis` | `skills/exemplar-review-analysis/SKILL.md` |
| `figure-permissions` | `skills/figure-permissions/SKILL.md` |
| `journal-selection` | `skills/journal-selection/SKILL.md` |
| `literature-screening` | `skills/literature-screening/SKILL.md` |
| `manuscript-polishing` | `skills/manuscript-polishing/SKILL.md` |
| `paper-deep-reading` | `skills/paper-deep-reading/SKILL.md` |
| `review-figures-and-tables` | `skills/review-figures-and-tables/SKILL.md` |
| `review-orchestrator` | `skills/review-orchestrator/SKILL.md` |
| `review-outline-builder` | `skills/review-outline-builder/SKILL.md` |
| `review-project-setup` | `skills/review-project-setup/SKILL.md` |
| `review-scoping-and-gaps` | `skills/review-scoping-and-gaps/SKILL.md` |
| `review-section-drafter` | `skills/review-section-drafter/SKILL.md` |
| `review-writing` | `skills/review-writing/SKILL.md` |
| `reviewer-response` | `skills/reviewer-response/SKILL.md` |
| `search-export-and-dedup` | `skills/search-export-and-dedup/SKILL.md` |
| `search-strategy-builder` | `skills/search-strategy-builder/SKILL.md` |
| `submission-package` | `skills/submission-package/SKILL.md` |
| `zotero-library-sync` | `skills/zotero-library-sync/SKILL.md` |

## Workflow

Start each session from `review-orchestrator` (`skills/review-orchestrator/SKILL.md`) to decide what step comes next. Route to exactly one next skill per turn. Do not start a second skill in the same turn. Inspect `project.yaml` and `LOG.md` to check stage gates (`topic_lock`, `search_lock`, `inclusion_lock`, `outline_lock`, `journal_lock`, `final_submit`). An earlier unpassed gate always beats a later file that already exists.

## Human gates

Gates are human checkpoints defined in `shared/gates.md`. A gate passes only when its key in `project.yaml` equals the YAML boolean `true`. Values like `false`, `"true"`, `yes`, or missing keys do not pass. The agent may record progress but must never confirm a gate for the user. Every confirmation entry in `LOG.md` must end with `| human`.

## Tests

```bash
python -m pytest -q
```

Open a terminal at the repository root and run pytest (the Python test runner) using the command above. CI runs the tests on several combinations of Python and pandas versions. Some skill tests require pandas.

## Editing skills

Keep `SKILL.md` frontmatter limited strictly to `name` and `description`. The `name` must match the skill directory name (using lowercase, digits, and hyphens). Keep each `SKILL.md` under 500 lines; place long templates inside `references/` (such as `skills/<name>/references/`). When a skill includes `skills/<name>/scripts/`, place matching tests under `skills/<name>/tests/`.
