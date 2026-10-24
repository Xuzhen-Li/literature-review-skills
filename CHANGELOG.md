# Changelog

## Unreleased

- AI-first literature flow is now the default. `skills/search-export-and-dedup/scripts/api_search.py` runs the locked search against OpenAlex, Europe PMC, PubMed, Semantic Scholar, and arXiv (Crossref on request), writes one dedup-ready CSV per source, and appends hit counts; `--count-only` gives feasibility counts. Tests use no network.
- `find_oa_pdfs.py` also looks up Europe PMC, Semantic Scholar, and arXiv, and tries the next source's link when a download fails.
- New `skills/zotero-library-sync/scripts/please_fetch.py`: from `fulltext_need.tsv` triage it lists only essential papers the agent could not get, ranked, with DOI and reason (`please_fetch.md`); the rest go to `abstract_only.tsv`.
- `institutional_access` is optional and no longer blocks routing. `project.yaml` defaults to `download_access: open_access` and adds `use_subscription_databases` and `use_zotero` (both `false`). Web of Science, Scopus, and Zotero collections are optional extras. Routing row 6 no longer waits for uploads or a collection checklist unless `use_zotero` is `true`.
- Add `scripts/check_skills.py` and `tests/test_check_skills.py` for portable `SKILL.md` frontmatter checks.
- Added `agents` to install targets.
- Added `--project DIR` flag to install into project-specific paths instead of `$HOME`.
- Added `.lrs-installed` marker file generation for copy mode installations.
- Changed `codex` target destination to `~/.agents/skills` instead of `~/.codex/skills`.
- Changed `all` target to install `cursor`, `claude`, and `agents`.
- `--uninstall` removes only this repository's symlinks and copies marked with `.lrs-installed`, so copies made before the marker existed are skipped.
- `--uninstall` also removes dangling symlinks named after a repository skill whose target ends in `/skills/<same name>`.
- The old `~/.codex/skills` directory is not cleaned automatically and can be deleted by hand.
- Added `skills/manuscript-polishing/scripts/export_refs.py` to export CSV and TSV spreadsheet tables to BibTeX and CSL-JSON formats, using the library file to fill missing author details.
- `skills/literature-screening/scripts/prisma_flow.py` draws a PRISMA 2020 flow diagram as SVG and PDF from a JSON or CSV counts file. It validates arithmetic and non-negative integers, supports an optional other-methods arm, includes example inputs under `references/prisma_flow_examples/`, and adds pytest coverage in `skills/literature-screening/tests/test_prisma_flow.py`.
- Added `asreview_io.py` script to export library records for ASReview LAB and import screening decisions back.
- Added `snowball.py` script to fetch backward and forward citations via OpenAlex with automatic retry and partial result saving.
- `plugin.json` and `.claude-plugin/plugin.json` version set to 0.3.0 to match this changelog.
- Clarified the `export_refs.py` `--csl` flag behavior, documented ASReview unlabelled records in `screening.csv`, explained the optional `LRS_CONTACT_EMAIL` and `--max-forward` limits, and updated Cursor plugin installation steps.

## 0.3.0 - 2026-10-13

- Narrative reviews keep the most relevant records up to `narrative_core_cap` in `project.yaml` (default 500). The agent does not change that number. Ties at the cutoff stay in the core and are logged. Other rows are `not_read` with reason `below-cap`. Systematic, scoping, and umbrella reviews still screen the full library.
- A published panel can be cropped from a PDF already on disk. `08-figures/panel_crop_ledger.csv` records the source, page, crop box, and copyright status. The same panel cannot be used twice. `needs-permission` does not become a publication file. An empty ledger writes nothing. Original SVG and PDF drawings remain the default.
- Before the project file is finished, the Web of Science homepage is opened, and PubMed's homepage is opened when PubMed will be searched. The gate is `institutional_access`.
- If the agent browser is not logged in, computer control may operate the user's own browser. The user types any password. The agent does not ask for it or store it.
- When this computer cannot download a paper, `04-library/doi_for_upload.tsv` lists the DOI and the user uploads the PDF. The suite does not fetch the file.
- Each skill says the paragraph in `shared/skill_intro.md` verbatim on first use.
- Gate replies must be the exact sentence in `shared/gates.md`. `yes` and `ok` do not pass.
- Changes already on main since 0.2.0 are included in this tag: `install.sh` copies `shared/` into each skill in copy mode; dedup DOI checks and install tests; CI for pytest and shellcheck; Claude Code, Codex, and Cursor plugin packaging; DOI and PMID checks in `verify_ids.py`.

## 0.2.0 - 2026-10-09

- Narrative reviews can rank the deduplicated library and keep a user-sized core. Records left out are logged as not read. Systematic, scoping, and umbrella reviews still use the full eligibility screen.
- Each original figure or table is written as an editable SVG plus a PDF. Fig. 1 stays an argument map. Published figures are not cropped.
- Outlines require separate limitations and next-questions sections. The section drafter will not call a draft finished while those sections are missing. Systematic outlines add a registration reminder and a bias-tool checklist, and they leave pooled estimates out unless the user asks.
- After journal lock, the style brief is refreshed from lawful reviews in that journal. Polishing applies its heading pattern, abstract shape, and figure budget before the word-processor export.
- Optional passes: wide, middle, and tight search strings when a hit count is extreme; post-export title clustering that may ask to reopen the topic lock; a Zotero collection checklist; note export only after the user asks; a national partition or citation metric copied from an official page opened that day; a cover-letter docx and an author-page field guide; highlights, using the count and character limit that page states, and a visual abstract as an original image only when that page requires them; decision cards that do not replace a yes or no lock.

## 0.1.0 - 2026-10-09

Initial release of the literature-review skill suite described in `docs/DESIGN.md`.

- Repository files: README, MIT license, `install.sh`, shared evidence schema, human gates, and writing rules.
- Skills 0-8: orchestrator, project setup, scoping, search strategy, export and deduplication, screening, Zotero sync, deep reading, and exemplar analysis.
- `skills/search-export-and-dedup/scripts/dedup.py` reads RIS, PubMed NBIB, and CSV exports and writes `library.csv` plus `prisma_counts.json`.
- `skills/literature-screening/scripts/kappa.py` computes Cohen's kappa for a dual-screener pilot.
- Skills 9-16 (outline through reviewer response) are part of this version's workflow and are specified in `docs/DESIGN.md`.
