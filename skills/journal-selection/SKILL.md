---
name: journal-selection
description: >
  Builds a shortlist of 3-5 journals that publish reviews, checked on each
  journal's official site and dated. Use when the user says "pick a journal",
  "shortlist journals", "where should we submit", "impact factor", "APC", or
  "lock the journal". Do not use to invent a journal title, copy a metric
  from a third-party ranking site, or submit the manuscript.
---

# Journal selection

## When to use

A full draft exists, or the user has asked for a journal before drafting and accepts that `manuscript-polishing` will still have to fit the locked journal's limits. Dynamic facts (scope, article types, APC, word limit, indexing, turnaround, impact factor) are written only after you open an official page, and each fact is dated.

## Inputs (paths) / Preconditions

- `<project>/project.yaml` — field, audience, review type.
- `<project>/07-outline/outline.md` — target word count and article type.
- `<project>/06-exemplars/style_brief.md` when present.
- `<project>/evidence/evidence_table.csv` — the `venue` column named in `shared/evidence_table_schema.md`, for included reviews.
- The user's own journal names, if they gave any.

`<suite>` and `<project>` are the suite directory and the review folder.

## Procedure (numbered steps)

1. Build the candidate list only from three places: names the user gave, journals that published the exemplars in `06-exemplars/`, and journals that published the review articles already in the evidence table. If that list has fewer than three real titles, ask the user for more names and stop. Do not add a title from memory, from a ranking blog, or from a search snippet.
2. For each candidate, open the publisher's author-guidelines page for that journal. Record the URL. Ignore Wikipedia, ResearchGate, library LibGuides, LetPub, SciRev, and social networks. Indexing and metrics have their own official pages, listed in `references/official_sources.md`.
3. Copy these facts from the page you opened, or write the token shown when the page does not state them:
   - article type name as printed (`Review`, `Systematic review`, or whatever the page calls it)
   - `accepts_reviews`: `yes` or `no`
   - `invited_only`: `yes` or `no`
   - OA model and APC, with the currency as printed, or `[VERIFY]`
   - word limit, or `[VERIFY]`
   - reference style, or `not stated`
   - turnaround, or `not stated` (do not import a number from a third-party site)
   - whether review is double-anonymized
4. Impact factor: write a number only if you saw it on the journal's own page or in Clarivate Journal Citation Reports opened in this session (https://jcr.clarivate.com/). Include the JCR year that was on screen. Otherwise write `Impact factor: [VERIFY]`. Put the factor in the `fit` cell or under the table, not as a reason to override scope.
5. Indexing: if the author page claims MEDLINE, Scopus, Web of Science, or DOAJ, confirm on the official list in `references/official_sources.md` and date that check too. If you did not open the list, the indexing cell is `[VERIFY]`.
6. Write `<project>/11-journal/journal_shortlist.md` with the table from `references/shortlist_template.md`. Three to five data rows. The `verified` cell is exactly:

`verified on YYYY-MM-DD at https://the-author-guidelines-url`

No tracking parameters. The date is the day you opened the page, not a date in the future.

7. Under the table, add:

```
Recommended: Journal Name
Backup: Other Journal Name
Double-anonymized: no
Reference style: Vancouver
```

`Recommended` and `Backup` must be different rows, both with `accepts_reviews` = `yes`. If `invited_only` is `yes`, add `Invitation for Journal Name: yes` only when the user has an invitation. Otherwise do not recommend that journal.

8. Run:

```
python3 <suite>/skills/journal-selection/scripts/check_shortlist.py \
  <project>/11-journal/journal_shortlist.md
```

Fix every `ERROR` until it prints `OK shortlist`.

9. Show the user the recommended journal, the backup, the word limit, the APC or `[VERIFY]`, and the guidelines URL. Do not edit `project.yaml` yet.

10. After the user locks the choice, record it with the gate name in `shared/gates.md` (fallback name `journal_lock`) without deleting other keys, and append:

`YYYY-MM-DD | journal-selection | journal lock passed: Journal Name | human`

## Human gate(s)

Journal lock. A passing checker is not the lock. If the user refuses, append `journal lock refused | human` and stop. `manuscript-polishing` does not start without the lock.

## Outputs (exact paths + formats)

- `<project>/11-journal/journal_shortlist.md` — the 12-column table plus the four lines in step 7.

## Quality checklist

- The checker prints `OK shortlist`.
- Every recommended journal was opened on an official author page, and the `verified` sentence matches that URL and today's date.
- No impact factor, APC, or turnaround number was copied from a third-party ranking or a search snippet.
- Invited-only journals are not recommended unless the invitation line is present.
- The file contains 3 to 5 journals, not a longer shopping list.

## Guardrails

- Do not invent ISSN, APC, impact factor, acceptance rate, or "time to first decision".
- Do not describe a journal as MEDLINE-indexed, DOAJ-listed, or "Q1" unless the official list was opened and the date is in the file.
- Do not submit, create an account, or write to an editor in this skill.

## Next step

`manuscript-polishing`, after the journal lock. If the locked word limit is below the outline target, polishing cuts to the limit and logs every cut. It does not reopen the science.
