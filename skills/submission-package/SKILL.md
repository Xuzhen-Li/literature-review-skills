---
name: submission-package
description: >
  Assembles the cover letter, title page, funding and conflict declarations,
  CRediT contributions, AI-use statement, suggested reviewers, and upload
  checklist for a locked journal. Use when the user says "cover letter",
  "submission package", "competing interests", "data availability", "CRediT",
  "suggested reviewers", or "ready to submit". Do not use to click Submit,
  sign a copyright transfer, pay an APC, or invent reviewer email addresses.
---

# Submission package

## When to use

The journal is locked, `10-polish/manuscript_polished.docx` exists, citation and overclaim checks passed, and `validate_ledger.py --strict` passed. You prepare files. The user uploads them.

## Inputs (paths) / Preconditions

- `<project>/11-journal/journal_shortlist.md` — locked journal, double-anonymized line, reference style, word limit.
- `<project>/10-polish/manuscript_polished.docx` and `manuscript.md`
- `<project>/08-figures/figure_ledger.csv` and `<project>/12-permissions/permissions_log.csv` if any item was reused or adapted
- `<project>/evidence/evidence_table.csv` for the data-availability statement
- Author names, affiliations, emails, funding, and conflicts, supplied by the user. If a fact is missing, leave the official placeholder and do not guess.
- Templates in `references/`
- ICMJE recommendations: https://www.icmje.org/recommendations/
- AI use by authors: https://www.icmje.org/recommendations/browse/artificial-intelligence/ai-use-by-authors.html
- COPE on AI authorship: https://publicationethics.org/guidance/cope-position/authorship-and-ai-tools
- CRediT roles: https://credit.niso.org/contributor-roles-defined/

`<suite>` and `<project>` are the suite directory and the review folder.

## Procedure (numbered steps)

1. Read the locked journal's author page again if the shortlist date is not today. Submission rules change. If the page disagrees with the shortlist, stop and update the shortlist before writing the letter.
2. Copy the five templates in `references/` into `<project>/13-submission/` under the same filenames: `cover_letter.md`, `title_page.md`, `declarations.md`, `suggested_reviewers.md`, `file_checklist.md`.
3. Cover letter, from `references/cover_letter.md`. One page, at most 500 words. It must say the manuscript is not under consideration elsewhere (ICMJE overlapping publication). Name the article type the journal actually uses. Do not claim the review is the first, do not mention an impact factor, and do not ask for a decision date.
4. Title page, from `references/title_page.md`. Author order and corresponding author come from the user. If the journal is `Double-anonymized: yes`, this file is separate and the manuscript file has no author names. Add that checklist line: `Manuscript contains no author names`. ORCID, if the user supplies one, is checked against https://orcid.org/ and must pass the checksum. Do not invent an ORCID.
5. Declarations, from `references/declarations.md`. Keep one funding paragraph and one AI paragraph.
   - No funding uses the sentence `No specific funding was received for this review.`
   - A grant needs the funder name and a number that the user provided.
   - No conflicts uses `The authors declare no competing interests.` Otherwise describe the interest in the author's words.
   - Data availability names the evidence table. Do not invent a repository DOI.
   - If no AI tool was used to draft, edit, or make figures, keep the no-AI sentence in the template. If one was used, replace that sentence with the disclosure block in the template comments: tool name, version, what it did, that humans take full responsibility, and that the tool is not an author (ICMJE and COPE, links above). Also put that disclosure in the cover letter and in the manuscript acknowledgements or methods, matching the journal.
   - CRediT roles are only the 14 names on https://credit.niso.org/contributor-roles-defined/. Optional degree is `lead`, `equal`, or `supporting`. Contribution lines use the same names, in the same order, as the title page. CRediT does not replace the four ICMJE authorship criteria: substantial contribution, drafting or critical revision, final approval, and accountability. AI tools are not authors.
6. Suggested reviewers, from `references/suggested_reviewers.md`. Default is 3 to 5 people. If the journal page states a number, set `Required count:` to that number and set `Rule source:` to `verified on YYYY-MM-DD at https://...`. If the page is silent, `Rule source: project default` and use the checks in the template: not a coauthor in the evidence table, not at an author institution, not a supervisor or student, no family link, has not seen this manuscript. Anyone you cannot check stays out of the suggested list. Put them under `## Do not suggest` with `Conflict check: unverified`. Email addresses come from an official staff page the user opened. Do not guess, and do not use an `example.com` address.
7. Checklist and upload order, from `references/file_checklist.md`. Follow the journal's upload order when the author page lists one. Tick a box only when that file exists. `Highlights: required` or `Highlights: not required` comes from the author page.
8. Run a draft check while placeholders remain, then the ready check:

```
python3 <suite>/skills/submission-package/scripts/check_package.py \
  <project>/13-submission --draft \
  --shortlist <project>/11-journal/journal_shortlist.md

python3 <suite>/skills/submission-package/scripts/check_package.py \
  <project>/13-submission \
  --shortlist <project>/11-journal/journal_shortlist.md
```

The second command is the ready check. It fails on placeholders, unchecked boxes, example emails, a cover letter over 500 words, and a title that does not match the title page.

9. Show the user the letter and the reviewer list. Do not upload.

10. After the user says the package is the one they will submit, append:

`YYYY-MM-DD | submission-package | final submit handed to the user | human`

Use the gate name in `shared/gates.md` when that file exists (fallback `final_submit`). You still do not log in.

## Human gate(s)

Final submit. The user logs in, uploads, pays any APC, and signs any copyright form. You stop when the ready check prints `OK submission package` and the user has the file list. You do not click Submit.

## Outputs (exact paths + formats)

- `<project>/13-submission/cover_letter.md`
- `<project>/13-submission/title_page.md`
- `<project>/13-submission/declarations.md`
- `<project>/13-submission/suggested_reviewers.md`
- `<project>/13-submission/file_checklist.md`

## Quality checklist

- The ready command prints `OK submission package`.
- Cover-letter title and corresponding-author email match the title page.
- Every author has at least one real CRediT role, and every role is one of the 14.
- Suggested reviewers are `Conflict check: clear`, with institutional emails the user verified.
- Permissions receipts exist for every non-original figure, or those figures were replaced.
- The manuscript file for a double-anonymized journal contains no author names.

## Guardrails

- Do not invent funding, conflicts, ORCIDs, reviewer names, or emails.
- Do not list an AI system as an author or cite an AI system as the source of a scientific claim.
- Do not promise the editor that the work is novel, first, or suitable for a fast track.
- Do not create a journal account or agree to a license.

## Next step

Stop. The user submits. When a decision letter arrives, use `reviewer-response`.
