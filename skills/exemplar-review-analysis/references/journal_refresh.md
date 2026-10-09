# Style-brief refresh

The first brief, written before a journal is locked, keeps `Refreshed after journal lock: no`. Polishing will not export until a later pass rewrites that line.

## After journal lock

Run this when `journal_lock` is true and the brief does not yet contain `Refreshed after journal lock: yes` for the recommended journal.

1. Ask the user for three to five lawful review PDFs published in the locked journal. Record the venue from the PDF. If the user can open fewer than three, say so in the brief and in `LOG.md` only after they accept that limit.
2. Do not choose those PDFs by an impact factor, a citation count, or any other metric you did not open on an official page that day.
3. Recount headings, body words, figures, tables, and reference-list length, or mark a cell `[VERIFY]` when the PDF text cannot be counted. Recount citation density only from numbers you calculated.
4. Rewrite `06-exemplars/style_brief.md`. Set these lines from that count, not from memory:
   - `Refreshed after journal lock: yes`
   - `Locked journal:` the recommended name in `11-journal/journal_shortlist.md`
   - `Heading pattern:` the heading order, separated by ` | `. If the exemplars have no limitations heading or no next-questions heading, add `Limitations` and `Next questions` and say in the structure section that this review added them.
   - `Abstract shape:` the moves you saw, separated by `; `, such as `background; aim; scope; roadmap`. Polishing looks for those labels in order as `**Background.**`.
   - `Figure budget:` a positive integer this manuscript will not exceed.
5. Append `YYYY-MM-DD | exemplar-review-analysis | style brief refreshed for <journal> from <N> reviews | agent`.

If the brief does not exist yet and the journal is already locked, this pass is the first brief. Do not write a second, conflicting file.

## From the included set

Only when the user asks. Use lawful PDFs they supply for records already in `03-screening/included.tsv`. Do not rank that set by an impact number. Rewrite the descriptive sections from those PDFs, set `Included-set refresh: yes`, and leave `Refreshed after journal lock` unchanged unless every PDF is from the locked journal and you are also doing the post-lock pass.
