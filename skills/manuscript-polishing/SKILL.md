---
name: manuscript-polishing
description: >
  Adapts a finished review draft to the locked journal: wording, consistency,
  overclaim hedging, citation audit, and a docx export. Use when the user
  says "polish the manuscript", "fit the word limit", "overclaim", "change
  log", or "export docx". Do not use to add results, add references, choose
  a journal, or respond to reviewers.
---

# Manuscript polishing

## Opening

On first use in a project, say this verbatim:

I am manuscript polishing. I fit the draft to the locked journal's style brief and I do not add claims.

## When to use

Every outline section has a checked draft, the journal lock has been passed, and `06-exemplars/style_brief.md` says `Refreshed after journal lock: yes` for that journal. This skill edits language and format. It does not add scientific claims.

## Inputs (paths) / Preconditions

- `<project>/11-journal/journal_shortlist.md` with `journal lock` already in `LOG.md`. Read the locked journal's word limit, reference style, and `Double-anonymized` line.
- `<project>/06-exemplars/style_brief.md` with `Refreshed after journal lock: yes`, a heading pattern, an abstract shape, and a figure budget.
- `<project>/09-draft/S*.md` and `<project>/07-outline/outline.md`.
- `<project>/evidence/evidence_table.csv`
- `<project>/08-figures/figure_ledger.csv`
- `shared/writing_rules.md`
- Phrase list: `references/overclaim_words.md`

Stop if the journal is not locked. Stop if any section file still fails `check_citations.py`.

## Procedure (numbered steps)

1. Assemble the section prose in outline order:

```
python3 <suite>/skills/manuscript-polishing/scripts/assemble_manuscript.py \
  --outline <project>/07-outline/outline.md \
  --drafts <project>/09-draft \
  --output <project>/10-polish/manuscript.md
```

2. Apply `06-exemplars/style_brief.md` before any other edit. Set the `##` headings to the `Heading pattern` line, in that order, including Limitations and Next questions. If the outline titles do not match that pattern, stop and ask the user to reopen the outline lock. Do not drop either required section. Write the abstract with the `Abstract shape` labels in order (`background` becomes `**Background.**`), using only claims already in the drafts. Keep the same evidence IDs. Unique `Fig. N` mentions must not exceed `Figure budget`. If the journal is double-anonymized, do not put author names, affiliations, or funding in this file. Those stay on the title page. Then run:

```
python3 <suite>/skills/manuscript-polishing/scripts/check_style_fit.py \
  --brief <project>/06-exemplars/style_brief.md \
  --manuscript <project>/10-polish/manuscript.md \
  --journal "<locked journal name>"
```

Do not continue while this command fails. Log heading and abstract edits as `structure` or `format` in the change log you create in the next step. Create that log before the edits if you need a row for them; an empty log with only the header is allowed until the first edit.

3. Create `<project>/10-polish/change_log.csv` with the header in `references/change_log_template.md` before the first edit. Every later edit gets a row. Allowed `change_type` values: `hedge`, `language`, `consistency`, `citation`, `format`, `structure`, `cut_to_limit`. There is no type for a new claim. `after` may be `[deleted]` only for `cut_to_limit` or `structure`.
4. If you drop an outline evidence ID, the reason cell must contain the words `dropped E014` (real ID). If you keep an ID, it stays in the manuscript as `(Smith, 2020; E014)` or, after you convert the style, as the formatted citation plus `<!-- E014 -->`.
5. Audit citations:

```
python3 <suite>/skills/review-section-drafter/scripts/check_citations.py \
  --manuscript <project>/10-polish/manuscript.md \
  --outline <project>/07-outline/outline.md \
  --change-log <project>/10-polish/change_log.csv \
  --evidence <project>/evidence/evidence_table.csv
```

6. Scan overclaims. Block phrases must be removed or hedged to match the evidence row. Review phrases (`significant`, `novel`, `robust`, and the rest of that list) stay only with a decision row.

```
python3 <suite>/skills/manuscript-polishing/scripts/polish_checks.py \
  <project>/10-polish/manuscript.md \
  --change-log <project>/10-polish/change_log.csv \
  --decisions <project>/10-polish/overclaim_decisions.tsv
```

`overclaim_decisions.tsv` is tab-separated: `line`, `phrase`, `decision`, `reason`. `decision` is `kept` or `removed`. A kept reason starts with `kept:` and names the evidence ID. Do not export while any block hit remains.

7. Fill `<project>/10-polish/consistency.md` from `references/consistency_checklist.md`. One row per term. Define an abbreviation at first use in the abstract and again at first use in the main text. Do not introduce an abbreviation you use fewer than three times.
8. Apply the locked journal's word limit by cutting, and log each cut. Do not delete the only citation for a sentence you keep. Match heading levels and spelling (US or UK) to the author guidelines. Reference style: convert each key from the evidence row's bibliographic fields. If a volume, page, or DOI is blank in the row, write `[VERIFY]` and do not invent it. Numbered styles still keep the `<!-- E014 -->` marker in the markdown.
9. Export only after `check_style_fit.py` has printed `OK style fit`. Pandoc (https://pandoc.org/MANUAL.html):

```
pandoc "<project>/10-polish/manuscript.md" \
  --from=markdown \
  --to=docx \
  --output="<project>/10-polish/manuscript_polished.docx"
```

If the user supplied the journal's own reference docx (not a file from an unofficial template site):

```
pandoc "<project>/10-polish/manuscript.md" \
  --from=markdown \
  --to=docx \
  --reference-doc="<project>/10-polish/reference.docx" \
  --output="<project>/10-polish/manuscript_polished.docx"
```

If `pandoc` is not installed, stop and ask the user to install it from https://pandoc.org/installing.html, or to run the python-docx fallback in `references/export_docx.md` themselves. Do not pip install.

10. After export, confirm the docx text has no `<!--` and no bare evidence-ID comments. Append:

`YYYY-MM-DD | manuscript-polishing | change log accepted | human`

only after the user has read the change log.

11. Open Terminal on macOS or PowerShell on Windows, then go to the repository folder with the cd command. Run the script to export your spreadsheet (CSV or TSV) records to BibTeX (a plain text format for references) and CSL-JSON (a structured data format for references) by typing:
```bash
python3 skills/manuscript-polishing/scripts/export_refs.py <project>/03-screening/included.tsv --library <project>/02-records/library.csv
```

Check the terminal output. Any citation key (a short text ID for a paper) listed in the authors_incomplete group will either end with "and others" in its BibTeX entry or have no author at all, and both situations need finishing by hand. Next, download the locked journal's CSL (Citation Style Language) file from https://github.com/citation-style-language/styles and use its saved file path for the --csl flag. You can then use Pandoc (a document converter) to format the citations. If you do not have Pandoc installed, you must first install it from https://pandoc.org/installing.html. Build the polished document by typing:
```bash
pandoc "<project>/10-polish/manuscript.md" \
  --from=markdown \
  --to=docx \
  --citeproc \
  --bibliography="<project>/03-screening/refs.bib" \
  --csl="<path_to_downloaded_journal.csl>" \
  --output="<project>/10-polish/manuscript_polished.docx"
```

## Human gate(s)

No separate project-level gate. The user accepts the change log before the docx is treated as the submission file. This is not the final submit gate.

## Outputs (exact paths + formats)

- `<project>/10-polish/manuscript.md`
- `<project>/10-polish/change_log.csv` — columns `id,file,location,change_type,before,after,reason`
- `<project>/10-polish/overclaim_decisions.tsv`
- `<project>/10-polish/consistency.md`
- `<project>/10-polish/manuscript_polished.docx`

## Quality checklist

- Both checkers print `OK`, and `check_style_fit.py` prints `OK style fit`.
- Headings, abstract labels, and the figure count follow the refreshed style brief.
- Every change-log `after` cell is free of block phrases.
- Every outline evidence ID is still cited, or its drop is logged as `dropped E###`.
- The manuscript cites no ID that is absent from the outline and the evidence table.
- Word count is within the locked journal's limit, or the limit cell was `[VERIFY]` and you stopped.
- The docx was produced by the pandoc command above, or by the documented python-docx fallback.

## Guardrails

- Do not add a finding, a citation, a sample size, or a mechanism that was not in the drafts.
- Do not strengthen a hedge. `indicates` does not become `shows` during polishing.
- Do not "fix" a reference by guessing page numbers or a DOI.
- Do not describe the prose as professionally copyedited unless a person did that. Language edits are logged as `language`.

## Next step

`figure-permissions` if any ledger row is still `adapted` or `reused` and not `granted`. Otherwise `submission-package`.
