# Writing rules

These rules bind every skill that writes prose, tables, or reviewer responses. Reporting follows PRISMA 2020 and, when a search is reported, PRISMA-S. Scoping reviews also follow JBI scoping guidance and PRISMA-ScR. Author responsibilities follow ICMJE (https://www.icmje.org/recommendations/). Research and publication integrity follow COPE (https://publicationethics.org/).

## Evidence binding

- A factual sentence in a draft maps to one or more `evidence_id` values in `evidence/evidence_table.csv`, or it is marked `[NEEDS SOURCE]`.
- `[NEEDS SOURCE]` may remain in a working draft. It must be gone before `final_submit`.
- Do not add a citation that has no evidence row. Do not add an evidence row that has no library record.
- Unknown DOI, PMID, author, year, journal, page, or statistic is `[VERIFY]`, never a guess.
- Polishing may rephrase. It may not add claims, citations, or numbers.

## Claim strength

Each evidence row has one `claim_strength`: `direct`, `indirect`, `conflicting`, or `background`. Draft wording uses the ladder below, which looks across the rows a paragraph actually cites. `review-section-drafter` enforces the same ladder.

| Level | When | Allowed | Not allowed |
|-------|------|---------|-------------|
| Established | Two or more independent `direct` rows and no `conflicting` row on that point | is, shows, has been reported | proves, conclusively, it is established |
| Supported | Two or more rows, or one systematic-review row, and the limitation is stated | indicates, is associated with | causes, leads to |
| Suggestive | One primary study, or only `indirect` rows | suggests, may, one study reported | is known to, clearly |
| Contested | A `conflicting` row is in the set | studies disagree, and both ids are cited | picking one side as fact |
| Background | `background` rows only | definitions and scope | empirical results |
| None | No row | do not write the sentence; `[NEEDS SOURCE]` | any factual claim |

A `cross-sectional` row does not support `causes` or `leads to`. In vitro, in silico, and animal designs stay labeled when the question is about another system. If `study_design` is empty, write `is associated with` and `[VERIFY design]`.

Citation shape in draft prose, using `first_author`, `year`, `n_authors`, and `evidence_id`:

```text
(Smith et al., 2020; E014)
(Smith and Lee, 2020; E014)
(Smith, 2020; E014)
```

`et al.` is for three or more authors. Do not invent the second author. If `n_authors` is empty, stop and fill it from the PDF or the export.

## Numbers

- Copy statistics from `statistic` or from the paper note. Keep units, sample size, and the comparison.
- Do not compute a new pooled effect in the draft. Pooling belongs in a methods section the user has chosen and is out of scope unless the outline says so.
- Dates of access for journal scope, impact factor, APC, word limits, and indexing are written next to the fact (`checked 2026-10-09`). Those facts expire. Re-check them on the official journal site before `journal_lock`.

## Quotations

- Prefer paraphrase.
- A quotation is at most one sentence, stored in the evidence row with a page, section, or figure id.
- Do not paste paragraphs from papers or from exemplar reviews.
- Figure ideas in reading notes are original redraws. They are not copies of published artwork.

## Figures

- Default type is `original`.
- `adapted` and `reused` need a source and a permission status before submission.
- Rights and licenses are checked by `figure-permissions` (publisher page, Creative Commons license on the article, or RightsLink via https://www.copyright.com/).
- Do not download or redraw a figure from an unauthorized copy.

## AI disclosure and authorship

- ICMJE: an AI tool is not an author. Do not put this suite, or any model name, on the author line.
- Disclose AI use where the target journal requires it. If the journal is silent, still record what the tool did in `13-submission/` and let the user decide the disclosure text. Do not decide that disclosure is unnecessary.
- COPE: do not suggest peer reviewers who are recent coauthors, same-institution colleagues, or people the user names as conflicts. If the conflict status is unknown, mark `[VERIFY]` and leave them off the suggested-reviewer list.

## Reviewer responses

- Number every comment.
- State the change location (section and paragraph) only after the manuscript file contains that change.
- If no change was made, say so and give the reason. Do not write "we have revised" for an unchanged sentence.
- Do not invent data, analyses, or citations to satisfy a reviewer.

## Language

Project files, templates, and agent-written outputs are English. Quotations from sources may remain in the source language only when the paper note also gives an English paraphrase and a page locator.
