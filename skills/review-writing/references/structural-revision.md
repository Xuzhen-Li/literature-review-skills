# Structural revision

## 1. Inventory (before any edit)

Record in a short inventory note:

- Parts present: title, abstract, highlights, keywords, introduction, heading levels, conclusion, declarations, references. Note any missing part.
- Counts: main-text words, level-1 sections, figures, tables, references, author comments.
- Figure and table check: every caption number has an in-text mention and vice versa (the script lists both for a .docx).
- Citation technology: Zotero (`ADDIN ZOTERO_ITEM CSL_CITATION`), EndNote (`ADDIN EN.CITE`), Mendeley, or plain text.
- Unfilled items: authors, affiliations, funding, conflicts of interest, data availability, placeholders such as `XXX`, `[ref]`, `TODO`.
- Backup path of the original.

### Comment table

Every author or co-author comment becomes a row. A comment is a request about the argument as often as about a word; classify it honestly.

| # | Location | Comment (short) | Issue type (logic / evidence / language / figure / format) | Action taken | Status (done / partly / open + reason) |
|---|----------|-----------------|------|------|------|

## 2. Diagnose the argument

Answer in writing before rewriting:

1. What core question does the review try to answer?
2. Which single sentence states the central judgement of the whole review?
3. What argumentative task does each level-1 section carry?
4. Are sections organized by scientific question, or paper by paper?
5. What content repeats?
6. Which paragraphs give background or citations but no judgement of the authors' own?
7. Where studies disagree, what is the real cause (conditions, design, measurement, time scale)?
8. Which conclusions are limited by design, sample handling, time scale, or measurement method?

### Revision blueprint (internal)

- Central claim (one sentence)
- Target reader
- Section logic map: section → task → judgement it ends with → open question it hands on
- Repeats to merge
- Evidence gaps (mark `[NEEDS SOURCE]` or narrow the claim)
- Key facts and inference limits that must survive the rewrite
- Cut / merge / move to supplement

Show the blueprint to the user before a large restructure when sections will be deleted or moved.

## 3. Rebuild sections around a problem or mechanism chain

Organize by process, mechanism, or question, never "Author A found… Author B found…". A typical chain, adapted to the topic:

phenomenon or problem → controlling mechanism → shared results across studies → where studies differ → why they differ → conditions of validity → meaning for assessment or future work

Do not force one set of headings on every review; pick the clearest chain for this subject.

Each section:

- opens by stating the question it settles;
- explains the mechanism and compares evidence in the middle;
- ends with its own judgement (not a recap);
- hands off to the next section through a question it leaves open.

## 4. Paragraph skeleton

Claim → Mechanism → Evidence → Boundary → Synthesis. It is a logic order, not five sentences. Short paragraphs may merge mechanism and evidence; a boundary appears only when it changes the conclusion.

Not this:

> Study A found X. Study B found Y. Study C also found X. However, Study D found the opposite.

This:

> Current evidence indicates that the process is controlled mainly by X and Y. Under condition A, several studies observed …; under condition B the response can reverse. The difference more likely reflects … than a true contradiction between studies.

When explaining differences, compare first the factors that actually vary between studies. For an environmental topic these are, for example: soil properties, contamination history, water status, drought or flooding duration, order of treatments, what was measured, operational definitions, time scale, and laboratory treatment versus field events. Substitute the equivalent factors for other fields.

## 5. Abstract, introduction, conclusion

Rebuild after the body.

**Abstract:** background → key problem or knowledge gap → scope of the review → core synthesis → environmental or research significance. No step-by-step methods, sample counts, or strings of numbers unless a number is the main finding.

**Introduction:** the scientific or pollution problem → why the disturbance or driver matters → what is known → why results disagree → the perspective this review takes → scope, central claim, and organization. It must end with the authors' own position, not "this review summarizes recent studies".

**Conclusion:** at least (1) a cross-section mechanistic judgement, (2) an explanation of why results differ, (3) what assessment, sampling, or future studies should change. Do not retell cases and numbers. Do not end with only "more research is needed".

## 6. Figures, tables, supplement

Figures lower the cost of understanding; they are not decoration. Main text usually keeps:

- one mechanism or concept overview figure;
- one data figure that supports the central judgement;
- one representative evidence table.

Move per-study design details, long data tables, and study-by-study lists to the supplement. Keep each figure with its caption, keep figure logic identical to the text, do not draw a near-identical schematic per section, do not copy published artwork without cleared rights (see `figure-permissions`), and prefer editable or code-generated figures. Do not spend figure time out of proportion to the information it adds.

## 7. Change log

One row per substantive change: location, type (structure / language / evidence-narrowed / figure / format / citation), before (short), after (short), reason. Pure wording changes inside a rewritten paragraph do not need their own rows.

## 8. Final QC checklists

**Content**
- The central claim runs through abstract, introduction, body, and conclusion.
- Every section ends with a clear judgement.
- No paragraph still lists studies one by one.
- No conclusion is repeated across sections.
- No new inference lacks support in the cited evidence.
- Every comment-table row has a status.

**Language** (see `anti-ai-style.md`)
- No template transitions; no runs of short sentences; no long noun stacks; no repeated identical caveats; a researcher outside the subfield can follow it.

**Technical**
- Field check passes and matches the baseline count (minus citations deliberately removed and logged).
- Figure and table numbers match in-text mentions; figures sit next to captions.
- No table split badly across pages; no heading stranded at a page bottom.
- No blank page, clipped text, odd font fallback, or blurred image.
- Hyperlinks and internal relationships valid.
- Bibliography free of HTML escapes (`&amp;`, `&lt;i&gt;`) and residual tags.
- No placeholder left (`XXX`, `TODO`, `[ref]`).
- Every rendered page image was opened and looked at.
