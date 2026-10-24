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

## Opening

On first use in a project, say this verbatim:

I am review project setup. I first ask whether you have a library account. If you do not, we use free open-access sources and nothing needs to be logged in. Then I create the project folder and project.yaml from your answers.

## When to use

No `project.yaml` exists yet, or the user asked to start a review. This skill builds the empty folder layout and records the interview. It does not lock the topic.

## Inputs (paths) / Preconditions

- A parent directory the user names. Create `<project>/` inside it. Do not scatter files outside that folder.
- The user's answers. If an answer is missing, ask once, then stop. Do not fill the gap from general knowledge.
- Copy the key names from `references/project.yaml.example`.

## Procedure (numbered steps)

1. Ask one question first: "Do you have a university or institute library login (Web of Science, Scopus, publisher access)?" If no, skip the homepage and go to step 2 with the open-access sentence. If yes, before any other project file, open the Web of Science homepage in the browser: https://www.webofscience.com/ . Do not type a password, a captcha, or a second factor. If the agent browser is not logged in, or it cannot open the page, use computer control of the user's own desktop browser when that tool is available, and let the user sign in. If neither browser can open the homepage, stop and ask the user to open it. After step 3, if PubMed will be searched, open https://pubmed.ncbi.nlm.nih.gov/ the same way before writing `project.yaml`.
2. Ask for one exact line. `I have confirmed institutional login` sets `download_access: institutional`. `I have no download permission on this computer` sets `download_access: unavailable`. `I will use open-access sources only` sets `download_access: open_access` (no account needed; PubMed and OpenAlex are free). Any other reply, including yes or ok, leaves `gates.institutional_access` false. Check with:

```bash
python3 <suite>/skills/review-orchestrator/scripts/check_gate_phrase.py \
  --gate institutional_access --reply "<user line>"
```

Use `--gate no_download_permission` for the second sentence and `--gate open_access_only` for the third. On a match, set `gates.institutional_access` to boolean `true`.
3. Ask, in one message, for: working title; field; review type (`narrative`, `systematic`, `scoping`, or `umbrella`); audience (who will read it); timeline; target journal or `undecided`; whether PubMed will be searched; and the project directory path. Do this only after step 2 has passed.
4. Restate the four review types in one line each before accepting the answer if the user is unsure:
   - narrative: a scoped argument, not an exhaustive search; the reading set is capped by `narrative_core_cap`
   - systematic: a pre-specified question, search, and eligibility screen (PRISMA 2020)
   - scoping: how much and what kind of evidence exists (JBI PCC; report with PRISMA-ScR)
   - umbrella: the included records are reviews, not primary studies
5. Create every directory below, plus `04-library/uploads/`. Create `LOG.md` and `project.yaml`. Do not create `evidence/evidence_table.csv` here; `paper-deep-reading` writes it with the header in `shared/evidence_table_schema.md`.

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

6. Write `project.yaml` from `references/project.yaml.example`. Set `narrative_core_cap` to `500` unless the user already typed a different positive integer in this interview. Do not change that number later. Set `search_pubmed` from their answer. Set `download_access` from step 2. Set `gates.institutional_access` to boolean `true` and every other gate to boolean `false`. Use today's date for `created` and `updated`. Set `language: en`. Quote any string that contains a colon.
7. Write `LOG.md` exactly as:

```text
# Decision log

Append-only. One decision per line. Do not delete lines.

YYYY-MM-DD | review-project-setup | project initialized | agent
```

8. Show the user the yaml. Ask: "Confirm this project file? Reply yes or no." On yes, append `YYYY-MM-DD | review-project-setup | project_confirmed | human`. On no, edit only the fields they correct, except `narrative_core_cap` and `gates.institutional_access`, and ask again.
9. Do not set `topic_lock`. The working title is not the locked angle.

## Human gate(s)

`institutional_access` before `project.yaml` is finished and before every later skill. The three accepted sentences are in `shared/gates.md`. A checker script does not replace the user's sentence. Confirming the yaml is a checkpoint, not a lock. Topic lock belongs to `review-scoping-and-gaps`.

## Outputs (exact paths + formats)

- `<project>/project.yaml` — keys in `references/project.yaml.example`
- `<project>/LOG.md` — header plus the lines above
- The fourteen numbered directories, plus `evidence/`

## Quality checklist

- `institutional_access` is YAML `true` only after an exact sentence. The other gate keys exist and are YAML `false`, not the string `"false"`.
- `narrative_core_cap` is a positive integer, `500` unless the user set it in the interview.
- `download_access` is `institutional`, `unavailable`, or `open_access`.
- `review_type` is one of the four allowed words.
- No search string, hit count, or citation appears in the yaml.
- `LOG.md` has the initialized line and, after a yes, the confirmed line.

## Guardrails

- Do not invent a journal, an impact factor, or a sample of papers.
- Do not ask for, type, or store a password, captcha, or second factor.
- Do not change `narrative_core_cap` after the project file is confirmed.
- Do not delete a project that already has a `LOG.md` with decisions. Ask the user before writing over `project.yaml`.
- Write only inside `<project>/`.

## Next step

`review-scoping-and-gaps`, after `institutional_access` is true and `project_confirmed` is in the log. Until then, stay here.
