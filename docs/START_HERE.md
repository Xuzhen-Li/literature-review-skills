# Start here

> Prose in this file is a structural draft. [待Gemini润色]

You do not have to start at step 1. Find the row that matches what you already have, and say the sentence in the last column to your AI tool (Claude Code, Cursor, Codex, ChatGPT, DeepSeek).

| What you have | Start with | Skip | Say this |
|---|---|---|---|
| Only a topic, no papers | `review-project-setup` | nothing | `start a new review on <topic>` |
| No library account (no Web of Science / Scopus) | `review-project-setup`, then answer `I will use open-access sources only` | Web of Science, Scopus, institutional login | `start a new review on <topic> using only free sources` |
| A set of papers already (PDF folder, Zotero collection, RIS/BibTeX, or a DOI list) | `review-project-setup`, then `search-export-and-dedup` with your file as `--source manual` | database searching (record in the methods that the set is user-supplied) | `I already have my papers in <path>; set up a review from them` |
| A draft (any state, .md or .docx) | `review-writing` | the whole pipeline; no `project.yaml` needed | `rewrite my review <path>; fix the logic` |
| A near-final manuscript | `journal-selection`, then `manuscript-polishing`, then `submission-package` | search, screening, drafting | `pick a journal for <path>` / `polish <path> for <journal>` |
| A decision letter | `reviewer-response` | everything else | `draft a response to these reviewer comments` |
| Not sure / mid-project | `review-orchestrator` | — | `what is the next step` |

## Getting papers without special accounts

1. Search free databases: PubMed (https://pubmed.ncbi.nlm.nih.gov/), OpenAlex (https://openalex.org/), Europe PMC (https://europepmc.org/). None needs a login; each exports RIS or CSV.
2. Merge and deduplicate: `python3 skills/search-export-and-dedup/scripts/dedup.py --input <file> --source pubmed ... --out-dir <project>/02-records`.
3. Find legal free PDFs for your included list (no account, no key):
   `python3 skills/zotero-library-sync/scripts/find_oa_pdfs.py <project>/03-screening/included.tsv -o <project>/04-library/oa_check.csv --download <project>/04-library/uploads`
   It accepts any CSV/TSV with a `doi` column, or a plain text list of DOIs. Setting `LRS_CONTACT_EMAIL` adds Unpaywall as a second source.
4. Papers still `closed`: your library, interlibrary loan, the preprint, or an email to the author. `pdf_handoff.py write` lists them with the file name to save as. Shadow libraries are never used.

Zotero is optional. It helps with collections and Word citations, but steps 1–4 work without it.

## Who does what (one job per skill)

| Stage | Skill | Its one job | Not its job |
|---|---|---|---|
| Entry | `review-orchestrator` | Read `project.yaml`, name the next skill | doing the work |
| Setup | `review-project-setup` | Create the folder and `project.yaml` | choosing the angle |
| Scope | `review-scoping-and-gaps` | Pick and lock the angle | search strings |
| Search | `search-strategy-builder` | Write and lock search strings | running exports |
| Records | `search-export-and-dedup` | Merge exports, deduplicate, PRISMA counts, check IDs, snowball | eligibility |
| Screening | `literature-screening` | Include/exclude with reasons | getting PDFs |
| Full text | `zotero-library-sync` | Get legal PDFs, track `pdf_status`, optional Zotero | reading |
| Reading | `paper-deep-reading` | Notes and evidence-table rows | writing prose |
| Style | `exemplar-review-analysis` | Style brief from 3–5 model reviews | outline |
| Outline | `review-outline-builder` | Section claims and lock | prose |
| Figures | `review-figures-and-tables` | Original figures, tables, ledger | permissions |
| Draft | `review-section-drafter` | First draft, one section at a time, from the evidence table | restructuring an existing draft |
| Revise | `review-writing` | Restructure and rewrite an existing draft; keep Word/Zotero fields live | new evidence, journal formatting |
| Journal | `journal-selection` | Shortlist and lock a journal | formatting |
| Polish | `manuscript-polishing` | Fit the locked journal, final language pass, export | rethinking structure |
| Permissions | `figure-permissions` | Licences for reused figures | drawing |
| Submit | `submission-package` | Cover letter, declarations, checklist | clicking Submit |
| Revision | `reviewer-response` | Point-by-point response | — |

Draft vs revise vs polish: **drafter** writes new text from an outline; **review-writing** fixes the argument of text that exists; **polishing** fits a finished argument to one journal.
