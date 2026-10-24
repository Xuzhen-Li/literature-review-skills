---
name: review-writing
description: >
  Revises an existing review manuscript (markdown or a Word .docx with Zotero
  or EndNote citations) whose logic is unclear, that lists papers one by one,
  reads as AI-written, has a weak abstract, introduction, or conclusion, or
  needs its figures and supplement reorganized. Diagnoses the argument first,
  then restructures, rewrites, protects live citation fields, and checks every
  rendered page. Use for "rewrite my review", "fix the logic", "it just lists
  studies", "AI flavour", "综述逻辑", "文献堆砌", "AI 味", "restructure the
  introduction/conclusion", "edit my review docx and keep the Zotero
  citations". Do not use for a single grammar question, plain translation,
  general journal information, or drafting a new review from an outline
  (use review-section-drafter).
---

# Review writing

## Opening

On first use in a project, say this verbatim:

I am review writing. I diagnose the argument before I touch sentences, I keep every citation field live, and I do not add evidence.

## When to use

The user has a review draft and wants it to read as an argued synthesis, not a list of studies. This skill works inside the suite (after `review-section-drafter`, before or alongside `manuscript-polishing`) and also on a standalone manuscript the user hands over. In a suite project, the evidence table and `shared/writing_rules.md` still bind every sentence. Outside a project, the manuscript's own citations are the evidence set.

## Pick the mode first

| Mode | Choose when | Steps used |
|------|-------------|------------|
| `language` | Sections and the argument already work; the user wants flow, clarity, and less template prose. | 1, 5, 7, 8 |
| `structural` | The central claim is unclear, sections follow papers instead of questions, content repeats, or the conclusion is thin. | 1–8 |
| `full-word` | The input is a .docx and the user wants the Word file itself revised, with citations, figures, comments, and references intact. | 1–8, with `references/docx-citation-safety.md` for every edit |

If the user asks to fix the logic, the structure, or "everything", do not fall back to `language`. Synonym swapping is never the job. A .docx input defaults to `full-word` unless the user asks only for text. State the chosen mode and why before step 2.

## Core workflow

1. **Inventory and back up.** Copy the original to `<name>.orig.docx` (or `.orig.md`) before anything else; never edit without a backup. Inventory sections, length, figures, tables, references, comments, live citation fields, and empty author/funding/COI items. For a .docx run `scripts/verify_docx_fields.py` and keep its output as the baseline. Turn every author comment into a row of the comment table. Details: `references/structural-revision.md` §1.
2. **Diagnose the argument.** Answer the eight diagnosis questions and write the revision blueprint (one-sentence central claim, reader, section logic map, repeats, evidence gaps, facts and inference limits to keep, what to cut, merge, or move to the supplement). `references/structural-revision.md` §2. Skip only in `language` mode.
3. **Rebuild the architecture.** Order sections along a problem or mechanism chain chosen for this topic. Each section opens with its question, compares evidence, and ends with a judgement that hands off to the next open question. §3.
4. **Group the literature by mechanism and question.** Studies that support one judgement are cited together; disagreements are explained by conditions, design, or measurement. §3–4.
5. **Rewrite paragraphs and sentences.** Claim, mechanism, evidence, boundary, synthesis as a logic skeleton, not five fixed sentences. Then apply `references/anti-ai-style.md`.
6. **Abstract, introduction, conclusion, figures, supplement.** Rebuild these after the body, from the blueprint. §5–6.
7. **Protect Word, Zotero, and the bibliography.** Every edit follows `references/docx-citation-safety.md`. Re-run the field check and compare to the baseline.
8. **Render every page and run final QC.** See Final verification.

## Non-negotiable rules

- Do not invent references, data, conditions, or conclusions. Do not turn correlation into causation, widen a study's scope, or drop units, time scales, temperatures, or treatment order. Full list: `references/evidence-integrity.md`.
- Do not add a new reference unless the user authorized a search and the record was verified against the original paper. Otherwise mark the gap `[NEEDS SOURCE]` and narrow the claim.
- Zotero `ADDIN CSL_CITATION` and `ADDIN CSL_BIBLIOGRAPHY` fields stay live. Never flatten them to plain text, never edit `itemData` by hand to change a source, and keep each `citationID` unique.
- If fields cannot be saved safely in the current environment, stop destructive edits to the .docx. Deliver revised text plus a replacement map instead.
- Do not claim a Zotero Refresh happened, or that the user's Zotero library changed, unless it did. Say plainly that Refresh in Word is still needed.
- Do not add errors, slang, or vagueness to look "less AI".

## When to read each reference

| File | Read before |
|------|-------------|
| `references/structural-revision.md` | Steps 1–4 and 6, and the comment table |
| `references/anti-ai-style.md` | Step 5 and the language QC |
| `references/evidence-integrity.md` | Any rewrite that changes a claim, merges studies, or explains a disagreement |
| `references/docx-citation-safety.md` | Opening, editing, or saving any .docx; page rendering |

## Final verification

1. Field check: `python3 <suite>/skills/review-writing/scripts/verify_docx_fields.py <revised>.docx --baseline <name>.orig.docx`. It must report balanced fields, unique citationIDs, parseable CSL JSON, no bibliography escapes, and no lost citation fields. Do not deliver while it prints `FAIL`.
2. Render every page: `soffice --headless --convert-to pdf --outdir <qc> <revised>.docx` then `pdftoppm -r 80 -png <qc>/<revised>.pdf <qc>/page`. Open each page image and check it. Opening the file, or looking at page 1 only, does not count.
3. Walk the content, language, and technical checklists in `references/structural-revision.md` §8 and record failures.

## Outputs

Keep deliverables apart from scratch files (scripts, page images, intermediate copies go in a `qc/` or temp folder outside the submission folder).

- Revised manuscript (`.docx` in `full-word`, else `.md`)
- Original backup (`*.orig.docx` / `*.orig.md`)
- `change_log` (short, one row per substantive change; in a suite project use `10-polish/change_log.csv` with `change_type` `structure` or `language`)
- Comment table (issue — action — status)
- Author-check list: unfilled items, `[VERIFY]` metadata, Zotero Refresh still needed, database errors (year, volume, author case)

## Next step

In a suite project, `manuscript-polishing` for journal fit and export when the journal is locked. Standalone, hand back the deliverables above.
