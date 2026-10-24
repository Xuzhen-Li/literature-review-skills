# Start here

You do not need to start from step 1. You can jump in with a draft, a folder of papers, or no university library account at all. Find the row below that matches what you have right now, and copy the sentence in the last column into your AI tool (Claude Code, Cursor, Codex, ChatGPT, or DeepSeek).

| What you have | Start with | Skip | Say this |
| --- | --- | --- | --- |
| Only a topic, no papers | `review-project-setup` | nothing | `start a new review on <topic>` |
| No library account (no Web of Science / Scopus) | `review-project-setup`, then answer `I will use open-access sources only` | Web of Science, Scopus, institutional login | `start a new review on <topic> using only free sources` |
| A set of papers already (Zotero collection, EndNote/Mendeley library, PDF folder, or a DOI list) | `review-project-setup`, then `search-export-and-dedup`: export the collection as RIS (Zotero: right-click collection > Export Collection > RIS); for a PDF folder, drag the PDFs into Zotero (it reads their metadata) and export RIS; for a DOI list, write a CSV with a `doi,title,year` header. Pass the `.ris` or `.csv` with `--source manual` (dedup.py reads only `.ris`, `.nbib`, `.txt` PubMed, and `.csv`) | database searching (record in the methods that the set is user-supplied) | `I already have my papers in <path>; set up a review from them` |
| A draft (any state, .md or .docx) | `review-writing` | the whole pipeline; no `project.yaml` needed | `rewrite my review <path>; fix the logic` |
| A near-final manuscript | `journal-selection`, then `manuscript-polishing`, then `submission-package` | search, screening, drafting | `pick a journal for <path>` / `polish <path> for <journal>` |
| A decision letter | `reviewer-response` | everything else | `draft a response to these reviewer comments` |
| Not sure / mid-project | `review-orchestrator` | none | `what is the next step` |

## Getting papers without special accounts

You do not need a university login or paid database subscriptions to run a review.

1. Search free databases: PubMed ([https://pubmed.ncbi.nlm.nih.gov/](https://pubmed.ncbi.nlm.nih.gov/)), OpenAlex ([https://openalex.org/](https://openalex.org/)), and Europe PMC ([https://europepmc.org/](https://europepmc.org/)). None of them need a login, and each one exports results as RIS or CSV.
2. Merge and remove duplicates:
   `python3 skills/search-export-and-dedup/scripts/dedup.py --input <file> --source pubmed ... --out-dir <project>/02-records`
3. Download legal free PDFs for your included list (no account or API key needed):
   `python3 skills/zotero-library-sync/scripts/find_oa_pdfs.py <project>/03-screening/included.tsv -o <project>/04-library/oa_check.csv --download <project>/04-library/uploads`
   This script accepts any CSV or TSV with a `doi` column, or a plain text list of DOIs. If you set the `LRS_CONTACT_EMAIL` environment variable, it also checks Unpaywall as a second source.
4. Get the remaining `closed` papers: try your library, interlibrary loan, a preprint server, or emailing the author. Run `pdf_handoff.py write` to list the missing papers and the exact file names to save them under. Shadow libraries are never used.

Zotero is optional. It helps manage collections and Word citations, but steps 1 to 4 work without it.

## Who does what (one job per skill)

| Stage | Skill | Its one job | Not its job |
| --- | --- | --- | --- |
| Entry | `review-orchestrator` | Read `project.yaml`, name the next skill | doing the work |
| Setup | `review-project-setup` | Create the folder and `project.yaml` | choosing the angle |
| Scope | `review-scoping-and-gaps` | Pick and lock the angle | search strings |
| Search | `search-strategy-builder` | Write and lock search strings | running exports |
| Records | `search-export-and-dedup` | Merge exports, deduplicate, PRISMA counts, check IDs, snowball | eligibility |
| Screening | `literature-screening` | Include/exclude with reasons | getting PDFs |
| Full text | `zotero-library-sync` | Get legal PDFs, track `pdf_status`, optional Zotero | reading |
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
