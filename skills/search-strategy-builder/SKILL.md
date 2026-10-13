---
name: search-strategy-builder
description: >
  Builds copy-pasteable PubMed, Web of Science, and Scopus search strings
  from the locked question, with field tags, a PRISMA-S block, and hit
  counts the user pastes, then stops for the search lock. Trigger on
  "write the search", "search string", "MeSH", "PRISMA-S", or "lock the
  search". Do not use it before the topic lock, and do not use it to
  export records or screen them.
---

# Search strategy builder

## Opening

On first use in a project, say this verbatim:

I am the search strategy builder. I write database strings from the locked question and I do not invent hit counts.

## When to use

`gates.topic_lock` is true and `00-scope/scope_report.md` has a `Locked question`. This skill writes the strategy. It does not download records.

## Inputs (paths) / Preconditions

- `<project>/00-scope/scope_report.md` — locked question and framework.
- `<project>/project.yaml` — `review_type`.
- Field tags in `references/database_syntax.md`. PRISMA-S items in `references/prisma_s_template.md`.
- PubMed tags: https://pubmed.ncbi.nlm.nih.gov/help/search-tags/
- MeSH: https://www.ncbi.nlm.nih.gov/mesh/
- PRISMA-S lives under https://www.prisma-statement.org/

If the topic is not locked, stop and return to `review-scoping-and-gaps`.

## Procedure (numbered steps)

1. Copy the locked question into `01-search/search_strings.md`. List one row per concept from the scope framework: concept, free-text synonyms, MeSH (PubMed), Emtree (only if Embase will be searched). A synonym you did not check against a record or a thesaurus is marked `candidate`.
2. Look up MeSH in the browser above. Record the descriptor, whether it is exploded (`[mh]`) or not (`[mh:noexp]`), and the entry terms you actually saw. If you did not open the page, write `MeSH: not looked up`. Do not invent a descriptor.
3. Emtree is for Embase, not for Scopus. If the user is not searching Embase, write `Emtree: not used`. If they are, use the syntax for the platform they named (Embase.com `'term'/exp` or Ovid `exp term/`) from `references/database_syntax.md`, and label the platform.
4. Write one fenced block per database the user can access, under a heading such as `## PubMed`, `## Web of Science`, or `## Scopus`. Default set is PubMed, Web of Science Core Collection, and Scopus. Drop a database the user cannot access and say why (PRISMA-S item 1). Do not add a database they did not agree to. Mark the string that will be run with `- Locked: yes`.
5. Tag terms. Untagged PubMed terms are subject to automatic term mapping; the saved string must be the one PubMed ran. After the user runs it, ask them to copy the line from Advanced search History (https://pubmed.ncbi.nlm.nih.gov/advanced/) into the file if it differs from the draft.
6. Put limits in a separate sentence under each block: date, language, publication type, human/animal. Cochrane Handbook chapter 4 (https://training.cochrane.org/handbook) treats limits as something to justify. Default is no language limit. A date limit needs a reason in the file (for example the question starts at a named event). Species hedges such as `animals[mh] NOT humans[mh]` are only for questions that need them. Do not paste that hedge into a plant or methods review.
7. Ask the user to run each locked string and paste, for each database: interface edition (WoS indexes selected; Scopus), the date, and the hit count. Record those rows in `01-search/hit_counts.tsv` with the header `database,interface,date,count,notes`. A count you did not receive is `[VERIFY]` in both files.
8. If a pasted count is below 20 or above 5000, or the user says it is too large or too small to screen, offer a wide string, a middle string, and a tight string as in `references/string_breadths.md`. Those two bounds are suite defaults, not a database rule. The user still locks exactly one. If they decline the extra strings, keep the single locked string and add `- Breadth declined:` plus their reason. Do not invent a hit count for a string that was not run. Then run:

```
python3 <suite>/skills/search-strategy-builder/scripts/check_strings.py \
  <project>/01-search/search_strings.md
```

`OK search strings` is required before the lock question.
9. Fill the 16 PRISMA-S items from `references/prisma_s_template.md` at the bottom of `search_strings.md`. Item 15 (totals) and item 16 (deduplication) stay `[VERIFY]` until `search-export-and-dedup` has run; say that, do not invent totals.
10. Note whether anyone peer-reviewed the strategy (PRESS 2015, McGowan et al., Journal of Clinical Epidemiology). If nobody did, item 14 says `not peer reviewed`.
11. Ask: "Pass search lock on the strings in 01-search/search_strings.md dated [today]? Reply with: I confirm the search lock."
12. On that exact sentence, only if no primary-database count is still `[VERIFY]`: set `gates.search_lock` to `true` and append `YYYY-MM-DD | search-strategy-builder | search lock passed | human`. On any other reply, edit and ask again.

## Human gate(s)

`search_lock`. Refuse to pass it while a database you claim to have searched still has `[VERIFY]` as its count, or while `check_strings.py` fails. Databases you explicitly did not search are allowed if the reason is written. An optional decision card may come first (`shared/decision_cards.md`): four labeled options, one preferred, and a custom option rewritten as a plan with its risks. Only the exact sentence sets the lock. The locked string is the one marked `- Locked: yes`.

## Outputs (exact paths + formats)

- `<project>/01-search/search_strings.md` — concepts, one locked fenced string per database (or wide, middle, and tight with exactly one locked), limits, PRISMA-S block.
- `<project>/01-search/hit_counts.tsv` — header `database,interface,date,count,notes`.

## Quality checklist

- Each fenced string uses only tags from `references/database_syntax.md` for that platform. Ovid syntax is not inside a PubMed block.
- Boolean operators are uppercase `AND`, `OR`, `NOT` (Scopus: `AND NOT`).
- MeSH terms that were not opened in the MeSH browser are absent, not guessed.
- `hit_counts.tsv` dates are the day the user ran the search.
- The locked strings match the History line when PubMed rewrote the query.
- `check_strings.py` prints `OK search strings`, with exactly one locked string per database.

## Guardrails

- Do not report a hit count from memory or from a "typical" range.
- Do not translate a PubMed string to WoS by swapping brackets only. Rebuild it with `TS=`, `TI=`, `DO=` and WoS proximity (`NEAR/n`).
- Do not start exporting files in this skill.
- Do not claim Embase and Scopus are the same database.

## Next step

`search-export-and-dedup` after `search_lock: true`.
