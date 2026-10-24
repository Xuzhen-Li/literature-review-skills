# PRISMA-S block

Copy this into `01-search/search_strings.md` and replace every bracket. Item wording follows the PRISMA-S checklist (16 items) published via https://www.prisma-statement.org/. If an item does not apply, write the reason. Do not delete the item.

```text
## PRISMA-S

1. Database name: [each database and its platform, for example OpenAlex (API), Europe PMC (REST API), PubMed (NCBI E-utilities), Semantic Scholar (Graph API bulk search), arXiv (API); optional Web of Science Core Collection (Clarivate) or Scopus (Elsevier)]
2. Multi-database searching: [platform name and the databases searched together, or "each database was searched separately"]
3. Study registries: [names, or "not searched" plus why]
4. Online resources and browsing: [what was browsed and how, or "none"]
5. Citation searching: [backward, forward, or "not done" plus why]
6. Contacts: [authors or experts contacted, or "none"]
7. Other methods: [hand search, grey literature, or "none"]
8. Full search strategies: [point to the fenced blocks above; they must be the strings that were run]
9. Limits and restrictions: [none, or each limit with a justification]
10. Search filters: [published filter citation, or "no published filter"]
11. Prior work: [review whose strategy was adapted, or "not adapted"]
12. Updates: [how an update will be run, or "not yet updated"]
13. Dates of searches: [YYYY-MM-DD per database, and the year span the string covered]
14. Peer review: [PRESS reviewer and date, or "not peer reviewed"]
15. Total records: [VERIFY until 02-records/prisma_counts.json exists; then copy identified_total and by_source]
16. Deduplication: [tool: skills/search-export-and-dedup/scripts/dedup.py; priority DOI, then PMID, then normalized title+year; fill duplicates_removed from prisma_counts.json]
```
