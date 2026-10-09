---
name: review-outline-builder
description: >
  Builds a thematic review outline with one claim per section, evidence IDs,
  planned figures, and a word budget that sums to the target. Use when the
  user says "make the outline", "outline the review", "section claims",
  "word budget", or "lock the outline". Do not use to draft prose, choose a
  journal, invent references, or redraw figures.
---

# Review outline builder

## When to use

The evidence table already has the papers that may be cited, and the topic lock has been passed. This skill turns those rows into a section map. It stops before any manuscript sentence is written.

## Inputs (paths) / Preconditions

- `<project>/project.yaml` — topic, review type (`narrative`, `systematic`, `scoping`, or `umbrella`), audience.
- `<project>/LOG.md`
- `<project>/evidence/evidence_table.csv` — ID column `evidence_id`, as named in `shared/evidence_table_schema.md`. IDs look like `E001` (at least three digits).
- `<project>/00-scope/scope_report.md`
- `<project>/05-reading/` notes for every ID you will attach to a section.
- `<project>/06-exemplars/style_brief.md` when that file exists. Use its section lengths as the starting budget, then make the budgets sum to the target.
- `shared/gates.md` and `shared/writing_rules.md`.

`<suite>` is the directory that contains this skill. `<project>` is the review folder created by `review-project-setup`.

Stop if the topic lock is not recorded. Do not create evidence IDs in this skill.

## Procedure (numbered steps)

1. Read the inputs. List the evidence IDs that are actually in the CSV. An ID that is only in a reading note and not in the CSV is not citable yet.
2. Group the IDs into themes. A theme that rests on one study must say so in its claim. Do not write a synthesis claim for a single row.
3. Copy `references/outline_template.md` to `<project>/07-outline/outline.md`. Delete the format-example claims. Keep this shape, including the hyphen bullets:

```
- Status: draft
- Review type: narrative
- Target words: 6000
- Date: YYYY-MM-DD

## Global claim

One sentence ending with a period.

## S1. Introduction

- Claim: One sentence ending with a period.
- Evidence IDs: E001, E002
- Word budget: 700
- Figures/tables: none
```

4. Set `Review type` from `project.yaml`. Systematic, scoping, and umbrella outlines need a section whose title contains `Method` (search reporting belongs there; item wording comes from the official PRISMA page you open, not from memory: https://www.prisma-statement.org/prisma-2020). Narrative outlines may omit Methods. Every review type also needs two different sections whose titles contain `Limitation` and `Next question`. Do not fold either into the conclusion. Each has its own claim and evidence IDs.
5. When `review_type` is systematic, copy `references/systematic_methods_checklist.md` to `<project>/07-outline/systematic_methods_checklist.md`. Keep the registration reminder and the bias-tool lines. A registry ID or a tool name stays `none yet` or `not chosen` until you open the official page and replace the source line with `Registry source: verified on YYYY-MM-DD at https://...` or `Official page: verified on YYYY-MM-DD at https://...`. RoB 2, ROBINS-I, and QUADAS-2 / QUADAS-3 are for different primary-study designs. AMSTAR 2 appraises systematic reviews, not primary studies. PROSPERO is only for eligible health-related systematic reviews. The checklist states which page to open. Leave pooling out. If the user asks for pooled estimates, set `Pooling: in scope` and `User asked: yes`, add `- Pooled estimates: in scope` to the outline, and name that work in a section title. Do not calculate a pooled number here.
6. Write the global claim and one claim per section. Each claim is a sentence the section will defend, no stronger than its weakest attached row. End each claim with a period.
7. `Evidence IDs` lists CSV IDs separated by commas. `none` is allowed only when the title starts with Acknowledgements, Acknowledgments, Funding, or Author contributions. For each ID on a section, set that evidence row's `outline_section` cell to the section id (`S1`, `S2`, ...). Do not add rows and do not change any other cell.
8. `Word budget` is an integer. Abstract, references, and figure legends stay outside the sum. Section budgets must add up to `Target words`. Take the target from the style brief when it gives one; otherwise set a body target and record why in `LOG.md`.
9. `Figures/tables` is `none` or a list such as `Fig. 1, Table 1`. Reserve `Fig. 1` for an original overview. Do not plan a copy of a published figure here; that decision belongs to the ledger.
10. Run the checker. Add `--checklist <project>/07-outline/systematic_methods_checklist.md` when the review is systematic.

```
python3 <suite>/skills/review-outline-builder/scripts/check_outline.py \
  <project>/07-outline/outline.md \
  --evidence <project>/evidence/evidence_table.csv
```

Fix every `ERROR` line until the command prints `OK outline`.

11. Show the user the global claim, the section titles, the evidence IDs, and the budget sum. Leave `Status: draft`.
12. Only after the user locks the outline, change the line to `Status: locked`, rerun the command with `--locked`, write the gate using the name in `shared/gates.md` (if that file is absent, use `outline_lock`) without deleting other `project.yaml` keys, and append one line to `LOG.md`:

`YYYY-MM-DD | review-outline-builder | outline lock passed | human`

## Human gate(s)

Outline lock. If the user refuses, append `outline lock refused | human` and stop. Do not start `review-section-drafter`. Changing a locked outline later requires the user to clear that lock in `LOG.md` first. An optional decision card may come first (`shared/decision_cards.md`): four labeled options, one preferred, and a custom option rewritten as a plan with its risks. Only a direct yes sets the lock.

## Outputs (exact paths + formats)

- `<project>/07-outline/outline.md` — markdown in the bullet shape above, including Limitations and Next questions.
- `<project>/07-outline/systematic_methods_checklist.md` when the review is systematic.

## Quality checklist

- `check_outline.py --locked` prints `OK outline` after the user agrees.
- Every non-structural section has at least one evidence ID that is in the CSV.
- The word budgets sum to `Target words`.
- Limitations and Next questions are separate sections, each with a claim and evidence IDs.
- No section claim states a number, mechanism, or priority that is not in the attached rows.
- Systematic, scoping, and umbrella outlines contain a Methods section.
- A systematic outline's checklist prints no errors, and it contains no pooled number unless the user asked and the outline says pooling is in scope.

## Guardrails

- Do not invent DOIs, PMIDs, authors, years, sample sizes, or results.
- Do not draft paragraphs, captions, or a reference list.
- Do not copy sentences from papers into the claim lines. A claim is your one-sentence synthesis, not a quotation.
- Do not mark the outline locked because the checker passed. The checker does not replace the user.

## Next step

`review-figures-and-tables`
