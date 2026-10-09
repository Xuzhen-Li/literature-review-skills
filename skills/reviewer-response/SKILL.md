---
name: reviewer-response
description: >
  Numbers every editor and reviewer comment, plans the action, and drafts a
  point-by-point response that cites the page and lines of each real change.
  Use when the user says "response to reviewers", "decision letter",
  "point by point", "R1.1", or "revise the manuscript". Do not use to invent
  comments, to claim a sentence was changed when it was not, or to submit
  the revision.
---

# Reviewer response

## When to use

The user has a decision letter and wants a revision, or the letter invites a response. The letter is saved verbatim before you number anything. You do not write a response to a comment that is not in that file.

## Inputs (paths) / Preconditions

- `<project>/14-revision/decision_letter.md`, `.txt`, or `.pdf` — pasted or saved by the user, unchanged. Read whichever of those three exists. Do not rename a `.txt` or `.pdf` the user already saved.
- The manuscript file you will actually change, usually `<project>/10-polish/manuscript.md`, plus the docx the journal will receive.
- `<project>/evidence/evidence_table.csv` if a new citation is required. A new citation still has to be a real row. If it is not in the table, stop and go back to `paper-deep-reading`. Do not invent one to satisfy a reviewer.
- `references/tone_guide.md` and `references/response_template.md`

If the letter is a rejection and does not invite revision, write `<project>/14-revision/decision_note.md` saying so, quote no comments you do not have, and stop. An appeal is a separate request. Read the journal's appeal policy first. Do not draft an appeal in this skill unless the user asks after that page has been opened.

## Procedure (numbered steps)

1. Read the letter. Split it into separate requests. Do not merge two requests into one number, and do not drop a criticism because it is inconvenient.
2. Number them in the letter's order. Editor comments are `E.1`, `E.2`, with no gaps. Reviewer 1 is `R1.1`, `R1.2`. Reviewer 2 is `R2.1`. If there is a reviewer 2, there is a reviewer 1. Editor comments come first when the letter has them.
3. Write `<project>/14-revision/action_plan.md` before you edit the manuscript. One heading per ID and one action bullet: `revised`, `declined`, or `clarified`. Show the plan to the user.
4. After the user accepts the plan, edit the manuscript. A `revised` action must change the file. A `declined` action must not. A `clarified` action changes the file only when you also use a revision phrase; otherwise it points the reviewer to text that is already there.
5. Turn on line numbers in the file you will submit before you write locations. Record both locators:
   - Source locator, for the checker: `10-polish/manuscript.md lines 40-44`
   - Letter locator, which the reviewer reads: `p. 3, lines 40-44`
   The page and line numbers are read off that file. Do not estimate them. If the docx has no line numbers yet, do not use the phrase "we have revised".
6. Write `<project>/14-revision/response_table.csv` with this header:

```
comment_id,action,location,change_quote,response
```

`location` is `none` when you did not edit. Otherwise it is the source locator. `change_quote` is the new text, at least a clause, and it must occur inside those lines. `response` is the paragraph the reviewer will read. For a revision it contains both a revision phrase (`we have revised`, `we have added`, `we have changed`, `we have deleted`, or `we have clarified`) and the page-line pattern `p. 3, lines 40-44`. It does not contain a project path such as `10-polish/`.

7. Write `<project>/14-revision/response.md` from `references/response_template.md`. Each section heading is the comment ID. The body contains the `response` cell verbatim. Follow `references/tone_guide.md`. Do not write "the reviewer misunderstood" unless you can point to the sentence they misread, and even then answer the request.
8. Run:

```
python3 <suite>/skills/reviewer-response/scripts/check_response.py \
  --table <project>/14-revision/response_table.csv \
  --letter <project>/14-revision/response.md \
  --plan <project>/14-revision/action_plan.md \
  --root <project>
```

The command fails if a revision phrase has no page and line, if the quoted new text is not in the cited lines, if a declined comment says you revised, or if the plan and the letter disagree. Fix the manuscript or the letter. Do not weaken the checker to make it pass.

9. Export the letter:

```
pandoc "<project>/14-revision/response.md" \
  --from=markdown \
  --to=docx \
  --output="<project>/14-revision/response_to_reviewers.docx"
```

Pandoc's manual is https://pandoc.org/MANUAL.html. If pandoc is missing, use the same fallback rule as `manuscript-polishing` (`skills/manuscript-polishing/references/export_docx.md`). Do not pip install.

10. Append `YYYY-MM-DD | reviewer-response | response checked against the revised file | agent` only when the command prints `OK response`. The user resubmits.

## Human gate(s)

Revision plan: do not edit the manuscript until the user accepts `action_plan.md`. If they refuse an action, change the plan, do not silently revise. Resubmission is the user's act. You do not log in.

## Outputs (exact paths + formats)

- `<project>/14-revision/action_plan.md`
- `<project>/14-revision/response_table.csv`
- `<project>/14-revision/response.md`
- `<project>/14-revision/response_to_reviewers.docx`
- The revised manuscript, with the quoted changes present at the cited lines

## Quality checklist

- The checker prints `OK response`.
- Every comment in the letter has one ID, and the IDs have no gaps.
- Every "we have revised" (and the other revision phrases) sits next to `p. N, lines N-N`, and the new wording is in the file at the source locator.
- Declined comments say what you did not change and why, with an evidence ID when the reason is scientific.
- The docx the journal receives does not contain `10-polish/` or other project paths.

## Guardrails

- Do not invent a reviewer comment, a compliment, or a change.
- Do not write "we have addressed all comments" as a substitute for the point-by-point table.
- Do not add data, a panel, or a citation that is not in the evidence table.
- Do not contact the reviewers outside the journal's system.
- A second round uses a new letter file and a new table. Do not reuse locations from the previous round after the file has moved.

## Next step

Stop. The user uploads the revised manuscript, the response docx, and any changed figures. If another letter arrives, run this skill again on that letter.
