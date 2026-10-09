---
name: exemplar-review-analysis
description: >
  Reads 3 to 5 recent reviews the user can legally open and writes a
  style brief: structure, section length, figure count, citation density,
  and tone. Trigger on "style brief", "exemplar reviews", "match the
  journal's reviews", or "how are reviews structured here". Do not use
  it to copy their prose, and do not use it before the included papers
  have notes.
---

# Exemplar review analysis

## When to use

Every included record has a reading note or a logged skip, and `06-exemplars/style_brief.md` does not exist yet. The user wants the outline skill to inherit a structure, not a paraphrase of someone else's review.

## Inputs (paths) / Preconditions

- `<project>/project.yaml` — `target_journal` and `review_type`.
- `<project>/00-scope/scope_report.md` — locked question, so exemplars can be judged for relevance.
- Three to five review PDFs the user already has legal access to, ideally from the target journal and published within the last five years. If `target_journal` is `undecided`, use reviews in the same field and mark the venue as provisional.
- Template: `references/style_brief_template.md`.

If the user cannot supply three PDFs, stop and ask. Do not select stand-in papers from memory and pretend they were read.

## Procedure (numbered steps)

1. Ask the user for 3 to 5 reviews (DOI or PDF). Record the DOI only as printed on the PDF. If it is unreadable, `[VERIFY]`.
2. For each PDF, count rather than estimate:
   - word count of the body, excluding references, or `[VERIFY]` if the PDF text layer is unusable (ask the user for the count)
   - heading list, in order
   - word count per major section, or `[VERIFY]`
   - number of figures and number of tables
   - number of citations in the reference list
   - citation density: citations per 1000 body words, rounded to one decimal, and only when both counts are numbers you calculated
3. Describe the pattern across the set in your own words: where the gap sentence sits, whether a methods section exists, how long the conclusion is relative to the body, and the grammatical person (`this review` versus `we`). Do not quote more than a short clause, and do not quote it if you can describe the pattern without it.
4. Note what not to copy: their sentences, their figures, their reference list, and any table that is a published data compilation.
5. Write `06-exemplars/style_brief.md` from the template. The "Implications" section is a constraint list for `review-outline-builder` (section order, a starting word budget, a figure budget). It is not an outline of this review's claims.
6. Append `YYYY-MM-DD | exemplar-review-analysis | style brief from <N> reviews | agent`.

## Human gate(s)

No project lock. If fewer than three exemplars were actually opened, do not write the brief. Ask the user for another PDF or for permission to proceed with the ones opened; if they accept fewer than three, record that in `LOG.md` (`style brief based on <N> reviews | human`) and state the limit in the brief.

## Outputs (exact paths + formats)

- `06-exemplars/style_brief.md` — sections in `references/style_brief_template.md`.

## Quality checklist

- Each exemplar row has a year and a venue taken from the PDF, or `[VERIFY]`.
- Word counts, figure counts, and citation counts are calculated or `[VERIFY]`, never a round number offered as a memory.
- Citation density is blank when either input count is `[VERIFY]`.
- The brief contains no paragraph copied from an exemplar.
- Implications name a word budget and a figure budget the outline skill can start from, and they say those numbers are a starting point.

## Guardrails

- Do not download an exemplar from an unauthorized copy.
- Do not treat an exemplar's citations as papers you have read. They are not added to the evidence table here.
- Do not adopt an exemplar's claim. Claims come from `evidence/evidence_table.csv`.
- Do not set `journal_lock` because several exemplars share a journal.

## Next step

`review-outline-builder`.
