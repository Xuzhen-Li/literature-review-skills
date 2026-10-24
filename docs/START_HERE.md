# Start here

You do not need to start from step 1. You can jump in with a draft or a folder of papers. You do not need a university library account. Find the row below that matches what you have right now, and copy the sentence in the last column into your AI tool (Claude Code, Cursor, Codex, ChatGPT, or DeepSeek).

| What you have | Start with | Skip | Say this |
| --- | --- | --- | --- |
| Only a topic, no papers | `review-project-setup` | nothing | `start a new review on <topic>` |
| You also want Web of Science or Scopus (optional) | `review-project-setup`, then say you have a library login | nothing | `start a new review on <topic>; I can also search Web of Science` |
| A set of papers already (Zotero collection, EndNote/Mendeley library, PDF folder, or a DOI list) | `review-project-setup`, then `search-export-and-dedup`: export the collection as RIS (Zotero: right-click collection > Export Collection > RIS); for a PDF folder, drag the PDFs into Zotero (it reads their metadata) and export RIS; for a DOI list, write a CSV with a `doi,title,year` header. Pass the `.ris` or `.csv` with `--source manual` (dedup.py reads only `.ris`, `.nbib`, `.txt` PubMed, and `.csv`) | database searching (record in the methods that the set is user-supplied) | `I already have my papers in <path>; set up a review from them` |
| A draft (any state, .md or .docx) | `review-writing` | the whole pipeline; no `project.yaml` needed | `rewrite my review <path>; fix the logic` |
| A near-final manuscript | `journal-selection`, then `manuscript-polishing`, then `submission-package` | search, screening, drafting | `pick a journal for <path>` / `polish <path> for <journal>` |
| A decision letter | `reviewer-response` | everything else | `draft a response to these reviewer comments` |
| Not sure / mid-project | `review-orchestrator` | none | `what is the next step` |

## How papers are found and downloaded

You do not need a university login, a paid database, or Zotero. By default, the agent searches and downloads papers itself:

1. Search: the agent runs the locked search through free APIs (OpenAlex, Europe PMC, PubMed, Semantic Scholar, arXiv; Crossref on request) and records the hit counts:
   `python3 skills/search-export-and-dedup/scripts/api_search.py --query '<string>' --out-dir <project>/02-records/raw --hit-counts <project>/01-search/hit_counts.tsv`
2. Merge and remove duplicates:
   `python3 skills/search-export-and-dedup/scripts/dedup.py --input <project>/02-records/raw/openalex_<date>.csv --source openalex ... --out-dir <project>/02-records`
3. Download legal open-access PDFs for the included papers (OpenAlex, Unpaywall when `LRS_CONTACT_EMAIL` is set, Europe PMC, Semantic Scholar, arXiv):
   `python3 skills/zotero-library-sync/scripts/find_oa_pdfs.py <project>/03-screening/included.tsv -o <project>/04-library/oa_check.csv --download <project>/04-library/pdfs`
4. The agent retries every paper the script could not download with its own browser or web-fetch tool: other open-access copies (repositories, preprints, Europe PMC / PMC, the publisher's PDF link). `agent_retry.py worklist` lists the candidate links and `agent_retry.py accept` takes in the PDFs it saved and records `got` or `failed` with a reason for each paper.
5. The agent marks which papers still missing are essential in `04-library/fulltext_need.tsv` and runs `please_fetch.py`. You get `04-library/please_fetch.md`, a short ranked list showing each paper's DOI, why it matters, and the file name to save it under in `04-library/uploads/`. Get what you can through your library, interlibrary loan, or the author. The review does not wait. Any paper you skip is cited from its abstract and noted as a limitation. Shadow libraries are never used.

Optional extras: Web of Science, Scopus, or Embase (set `use_subscription_databases: true` and reply with the `institutional_access` sentence), and Zotero collections (`use_zotero: true`). Steps 1 to 4 do not need them.

## Who does what (one job per skill)

| Stage | Skill | Its one job | Not its job |
| --- | --- | --- | --- |
| Entry | `review-orchestrator` | Read `project.yaml`, name the next skill | doing the work |
| Setup | `review-project-setup` | Create the folder and `project.yaml` | choosing the angle |
| Scope | `review-scoping-and-gaps` | Pick and lock the angle | search strings |
| Search | `search-strategy-builder` | Write search strings, get the counts from free APIs, lock them | downloading records |
| Records | `search-export-and-dedup` | Download records from free APIs, add optional exports, deduplicate, PRISMA counts, check IDs, snowball | eligibility |
| Screening | `literature-screening` | Include/exclude with reasons | getting PDFs |
| Full text | `zotero-library-sync` | Download OA PDFs, write the please-fetch list, track `pdf_status`, optional Zotero | reading |
| Reading | `paper-deep-reading` | Notes and evidence-table rows | writing prose |
| Style | `exemplar-review-analysis` | Style brief from 3 to 5 model reviews | outline |
| Outline | `review-outline-builder` | Section claims and lock | prose |
| Figures | `review-figures-and-tables` | Original figures, tables, ledger | permissions |
| Draft | `review-section-drafter` | First draft, one section at a time, from the evidence table | restructuring an existing draft |
| Revise | `review-writing` | Restructure and rewrite an existing draft; keep Word/Zotero fields live | new evidence, journal formatting |
| Journal | `journal-selection` | Shortlist and lock a journal | formatting |
| Polish | `manuscript-polishing` | Fit the locked journal, final language pass, export | rethinking structure |
| Permissions | `figure-permissions` | Licences for reused figures | drawing |
| Submit | `submission-package` | Cover letter, declarations, checklist | clicking Submit |
| Revision | `reviewer-response` | Point-by-point response | none |

How the three writing skills differ: `review-section-drafter` writes new sections from an outline and evidence table; `review-writing` rewrites and fixes the logic of a draft you already have; `manuscript-polishing` formats and edits a finished manuscript for a specific journal.
