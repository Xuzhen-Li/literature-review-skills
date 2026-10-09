# Response letter

The CSV is the source the checker reads. This markdown file is what pandoc exports. Copy each `response` cell under its heading. Do not add project paths.

```
# Response to reviewers

We thank the editor and the reviewers. The replies below use the line numbers
in the revised manuscript.

## E.1

The search date is already stated in the Methods, and that sentence can stand.

## R1.1

We have revised the sentence on p. 3, lines 40-44 so the wording matches the
two trials. Evidence from two field trials indicates a yield gain.

## R1.2

We have not changed this paragraph. The requested analysis is outside the
stated scope of the review.
```

Matching `response_table.csv` columns:

```
comment_id,action,location,change_quote,response
```

- `revised` rows: `location` is `10-polish/manuscript.md lines 40-44`, `change_quote` is the new text inside those lines, and `response` contains `we have revised` (or `we have added`, `we have changed`, `we have deleted`, `we have clarified`) plus `p. 3, lines 40-44`.
- `declined` rows: `location` and `change_quote` are `none`. The response must not say the text was revised.
- `clarified` rows with no edit use `none` as well. If the clarification changed the file, treat it as a revision: page, line, and quote.

`action_plan.md` uses the same headings and `- Action: revised` (or `declined`, or `clarified`) before you edit.
