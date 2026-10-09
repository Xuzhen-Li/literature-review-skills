---
name: review-project-setup
description: >
  Creates the review project folder, interviews the user for topic, field,
  review type, audience, and timeline, and writes project.yaml plus LOG.md.
  Trigger on "start a new review on X", "new literature review", or "set up
  the review project". Do not use it to choose the final angle, write a
  search, or draft the manuscript.
---

# Review project setup

## When to use

No `project.yaml` exists yet, or the user asked to start a review. This skill builds the empty folder layout and records the interview. It does not lock the topic.

## Inputs (paths) / Preconditions

- A parent directory the user names. Create `<project>/` inside it. Do not scatter files outside that folder.
- The user's answers. If an answer is missing, ask once, then stop. Do not fill the gap from general knowledge.
- Copy the key names from `references/project.yaml.example`.

## Procedure (numbered steps)

1. Ask, in one message, for: working title; field; review type (`narrative`, `systematic`, `scoping`, or `umbrella`); audience (who will read it); timeline; target journal or `undecided`; and the project directory path.
2. Restate the four review types in one line each before accepting the answer if the user is unsure:
   - narrative: a scoped argument, not an exhaustive search
   - systematic: a pre-specified question, search, and eligibility screen (PRISMA 2020)
   - scoping: how much and what kind of evidence exists (JBI PCC; report with PRISMA-ScR)
   - umbrella: the included records are reviews, not primary studies
3. Create every directory below and an empty placeholder is not required inside them. Create `LOG.md` and `project.yaml`. Do not create `evidence/evidence_table.csv` here; `paper-deep-reading` writes it with the header in `shared/evidence_table_schema.md`.

```text
<project>/
  project.yaml
  LOG.md
  00-scope/
  01-search/
  02-records/
  03-screening/
  04-library/
  05-reading/
  evidence/
  06-exemplars/
  07-outline/
  08-figures/
  09-draft/
  10-polish/
  11-journal/
  12-permissions/
  13-submission/
  14-revision/
```

4. Write `project.yaml` with every gate set to boolean `false`. Use today's date for `created` and `updated`. Set `language: en`. Quote any string that contains a colon.
5. Write `LOG.md` exactly as:

```text
# Decision log

Append-only. One decision per line. Do not delete lines.

YYYY-MM-DD | review-project-setup | project initialized | agent
```

6. Show the user the yaml. Ask: "Confirm this project file? Reply yes or no." On yes, append `YYYY-MM-DD | review-project-setup | project_confirmed | human`. On no, edit only the fields they correct and ask again.
7. Do not set `topic_lock`. The working title is not the locked angle.

## Human gate(s)

Checkpoint only: the user confirms `project.yaml`. That confirmation is not one of the six locks. Topic lock belongs to `review-scoping-and-gaps`.

## Outputs (exact paths + formats)

- `<project>/project.yaml` — keys in `references/project.yaml.example`
- `<project>/LOG.md` — header plus the lines above
- The fourteen numbered directories, plus `evidence/`

## Quality checklist

- All six gate keys exist and are YAML `false`, not the string `"false"`.
- `review_type` is one of the four allowed words.
- No search string, hit count, or citation appears in the yaml.
- `LOG.md` has the initialized line and, after a yes, the confirmed line.

## Guardrails

- Do not invent a journal, an impact factor, or a sample of papers.
- Do not delete a project that already has a `LOG.md` with decisions. Ask the user before writing over `project.yaml`.
- Write only inside `<project>/`.

## Next step

`review-scoping-and-gaps`, after `project_confirmed` is in the log. Until then, stay here.
