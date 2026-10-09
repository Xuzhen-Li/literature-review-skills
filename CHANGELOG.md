# Changelog

## 0.1.0 - 2026-10-09

Initial release of the literature-review skill suite described in `docs/DESIGN.md`.

- Repository files: README, MIT license, `install.sh`, shared evidence schema, human gates, and writing rules.
- Skills 0-8: orchestrator, project setup, scoping, search strategy, export and deduplication, screening, Zotero sync, deep reading, and exemplar analysis.
- `skills/search-export-and-dedup/scripts/dedup.py` reads RIS, PubMed NBIB, and CSV exports and writes `library.csv` plus `prisma_counts.json`.
- `skills/literature-screening/scripts/kappa.py` computes Cohen's kappa for a dual-screener pilot.
- Skills 9-16 (outline through reviewer response) are part of this version's workflow and are specified in `docs/DESIGN.md`.
