# Changelog

## Unreleased

- `install.sh` copy mode copies the repository `shared/` directory into each destination skill as `<name>/shared/` and fails if `shared/` is missing.
- Corrected the deduplication pandas test fixture DOI from `10.1/Beta` to `10.1000/Beta` and added `test_doi_needs_four_digit_registrant` and `test_pandas_csv_path_keeps_all_fields` in `skills/search-export-and-dedup/tests/test_dedup.py`.
- Added `tests/test_install.py` to verify copy and link shared file resolution, repeatable copy installations, and that `--dry-run` writes nothing.
- Added a CI workflow with a `pytest` matrix for Python 3.10 and 3.13 against pandas none, `pandas<3`, and `pandas>=3` (excluding Python 3.10 with `pandas>=3`), alongside an install job for shellcheck and link/copy smoke tests.
- Add `.claude-plugin/plugin.json` and `.claude-plugin/marketplace.json` for Claude Code plugin installation via `/plugin marketplace add` and `/plugin install`.
- Add root `plugin.json` using the Agent Plugins 1.0.0 schema and `.agents/plugins/marketplace.json`.
- Document Codex installation via `codex plugin marketplace add` and Cursor local clone path.
- Added `agents` to install targets.
- Added `--project DIR` flag to install into project-specific paths instead of `$HOME`.
- Added `.lrs-installed` marker file generation for copy mode installations.
- Changed `codex` target destination to `~/.agents/skills` instead of `~/.codex/skills`.
- Changed `all` target to install `cursor`, `claude`, and `agents`.
- `--uninstall` removes only this repository's symlinks and copies marked with `.lrs-installed`, so copies made before the marker existed are skipped.
- `--uninstall` also removes dangling symlinks named after a repository skill whose target ends in `/skills/<same name>`.
- The old `~/.codex/skills` directory is not cleaned automatically and can be deleted by hand.

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
