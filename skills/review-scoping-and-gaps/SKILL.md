---
name: review-scoping-and-gaps
description: >
  Turns a working title into three candidate angles, a gap statement, and a
  feasibility count from free database APIs, then recommends one
  angle and stops for the topic lock. Trigger on "scope the review",
  "find the gap", "which angle", "lock the topic", or "cluster the
  export". Do not use it to write the full search strategy, screen
  papers, or draft sections. The cluster pass does not replace the
  topic lock.
---

# Review scoping and gaps

## Opening

On first use in a project, say this verbatim:

I am review scoping and gaps. I compare candidate angles against the locked review type and I stop at the topic lock until you use the exact sentence.

## When to use

`project.yaml` exists and `topic_lock` is not true. The product is `00-scope/scope_report.md`, not a search string and not a manuscript outline. After `02-records/library.csv` exists, also use this skill when the user asks for the cluster pass in step 9. That pass does not clear `topic_lock`.

## Inputs (paths) / Preconditions

- `<project>/project.yaml` with `review_type`, `topic`, `field`, and `audience`.
- `<project>/LOG.md`.
- Framework definitions in `references/question_frameworks.md`.
- Free APIs for the feasibility count: `skills/search-export-and-dedup/scripts/api_search.py --count-only` (PubMed and OpenAlex; no login).

If `review_type` is empty, return to `review-project-setup`.

## Procedure (numbered steps)

1. Read the working topic. Write the question in the framework that matches `review_type` (table in `references/question_frameworks.md`). Leave a cell as `[VERIFY]` rather than inventing a population or outcome the user did not name.
2. Propose three angles. Each angle gets: a one-sentence question, what it includes, what it excludes, and why a reader in `audience` would care. At least one angle must be narrower than the working title. Do not propose an angle that would require data the user has already said they lack.
3. For each angle, write a gap statement in this shape: "Reviews to date cover X; they do not answer Y; this angle would answer Y by Z." If you cannot name X from a paper you opened in this session, write `X: [VERIFY]` and list the search you want the user to run. Do not cite a review you did not open.
4. Feasibility is an actual database count, not an estimate. For each angle, build a short PubMed query using `[tiab]` and (if you looked up a term at https://www.ncbi.nlm.nih.gov/mesh/) one `[mh]` term, plus the same query in plain words for OpenAlex. Run the counts yourself:

```bash
python3 <suite>/skills/search-export-and-dedup/scripts/api_search.py --count-only \
  --sources pubmed,openalex --pubmed-query '<PubMed query>' --openalex-query '<OpenAlex query>'
```

Record each printed total with today's date and the source name. If a source fails, retry once. If it fails again, give the user `https://pubmed.ncbi.nlm.nih.gov/?term=<url-encoded query>` and ask them to paste the count and date. Until you have a count from either route, mark the cell as `[VERIFY]`. Never write a number that did not come from the script output, a page opened in this session, or the user's message.

5. Recommend one angle in a short paragraph: fit to review type, a non-`[VERIFY]` count if one exists, and the narrowest question that still has enough records to discuss. If every count is `[VERIFY]`, recommend an angle but say the recommendation is provisional.
6. Write `00-scope/scope_report.md` with these headings: `Review type`, `Framework`, `Angle A`, `Angle B`, `Angle C`, `Feasibility`, `Recommendation`, `Out of scope`, `Gate`.
7. Ask: "Pass topic lock on angle [letter]: [title]? Reply with: I confirm the topic lock."
8. On that exact sentence: set `gates.topic_lock` to `true`, set `updated` to today, put the locked question at the top of the report under `Locked question`, and append:

```text
YYYY-MM-DD | review-scoping-and-gaps | topic lock passed: angle <letter> | human
```

On no: revise the rejected part and ask again. Do not lock.

9. Optional, and only after `02-records/library.csv` exists and the user asks: cluster titles and abstracts. This does not replace steps 1–8 and it does not clear `topic_lock` by itself.

```
python3 <suite>/skills/review-scoping-and-gaps/scripts/cluster_export.py \
  --library <project>/02-records/library.csv \
  --question "<locked question>" \
  --out <project>/00-scope/export_clusters.md
```

The groups are token overlap, not a new topic. If the file asks whether to reopen the topic lock, ask the user. Clear `topic_lock` only after they say yes to reopening it, and then rewrite the scope report from step 1. Do not treat the cluster file as the lock.

## Human gate(s)

`topic_lock`. The working title in `project.yaml` is not this gate. A feasibility count of zero blocks the lock until the user picks a different angle or explicitly accepts a conceptual review with the count written as `0` from the script output or their paste. An optional decision card may come first (`shared/decision_cards.md`): four labeled options, one preferred, and a custom option rewritten as a plan with its risks. Only the exact sentence sets the lock.

## Outputs (exact paths + formats)

- `<project>/00-scope/scope_report.md` — headings in step 6, plus `Locked question` after a yes.
- `<project>/00-scope/export_clusters.md` only when the user asked for the post-export pass.
- Updates to `project.yaml` (`topic_lock`, `updated`, and `topic` set to the locked question) and one `LOG.md` line.

## Quality checklist

- Three angles are present, and one is recommended.
- Every hit count is an integer from `api_search.py` or a user paste, with a date, or the token `[VERIFY]`.
- The framework matches `review_type`.
- Out-of-scope items are concrete (population, year span, or study design), not "everything else".
- The gate is still false in the yaml until the user says yes.

## Guardrails

- Do not run the full multi-database search. That is `search-strategy-builder`.
- Do not invent MeSH terms. If you did not open the MeSH browser, the controlled-vocabulary cell says `not looked up`.
- Do not cite a PMID, DOI, or paper title you did not open.
- Cochrane search guidance is Handbook chapter 4 (https://training.cochrane.org/handbook). JBI scoping questions use PCC (https://jbi-global-wiki.refined.site/space/MANUAL). Do not claim a chapter said something you did not read.

## Next step

`search-strategy-builder` after `topic_lock: true`. If the user said no, stay in this skill.
