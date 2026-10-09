---
name: review-section-drafter
description: >
  Drafts one review section at a time from the locked outline and the
  evidence table, with citation keys and hedging matched to the evidence.
  Use when the user says "draft the introduction", "draft section", "write
  the next section", or "hedge this claim". Do not use to polish for a
  journal, invent references, write the cover letter, or draft a section
  whose outline claim is not locked.
---

# Review section drafter

## When to use

`07-outline/outline.md` says `Status: locked`, and the user has named one section. Draft only that section. A later section waits until this file passes the checker.

## Inputs (paths) / Preconditions

- `<project>/07-outline/outline.md` — the `## S<n>` block you were asked to draft.
- `<project>/evidence/evidence_table.csv` and the `05-reading/` note for each ID on that block.
- `<project>/08-figures/figure_ledger.csv` when the section names a figure.
- `shared/evidence_table_schema.md`, `shared/writing_rules.md`.

Stop if the outline is not locked. Stop if a named evidence ID is missing from the CSV. Do not add rows to the evidence table here.

## Procedure (numbered steps)

1. Copy the section's claim, evidence IDs, word budget, and figure list into a new file `<project>/09-draft/S0N-title-slug.md`. `N` is the outline number zero-padded to two digits. The slug is the title in lowercase ASCII, spaces turned into hyphens. Header, then prose:

```
# S2. Shared findings

- Outline claim: Two independent lines of evidence agree on the direction of the effect.
- Word budget: 1800
- Evidence IDs: E002, E003
- Status: draft

## Prose
```

2. Read only the evidence rows and reading notes named in that header. Do not use a paper that is not on the list. If the section needs another paper, stop and reopen the outline lock. Do not cite it "just this once".
3. Write the prose under `## Prose` in paragraphs. Each paragraph that states a result uses this order:
   1. Topic sentence: the point of the paragraph, hedged to the weakest evidence it needs.
   2. Synthesis: what at least two sources agree on, with both citation keys, unless only one source exists.
   3. Critical comparison: where those sources differ in design, population, or result. If there is only one source, this sentence says it is a single study.
   4. Implication for the section claim. Do not add a new fact in this sentence.
4. Match the verb to the evidence. This is the same ladder as `shared/writing_rules.md`. "Rows" means evidence-table rows. The design is the `study_design` column in `shared/evidence_table_schema.md`. If that cell is empty, use the design line in the reading note.

| Level | When | Wording you may use | Wording you do not use |
| --- | --- | --- | --- |
| Established | Two or more independent `direct` rows and no `conflicting` row on that point | is, shows, has been reported | proves, conclusively, it is established |
| Supported | Two or more rows, or one `systematic-review` row, and the limitation is stated | indicates, is associated with | causes, leads to |
| Suggestive | One primary study, or only `indirect` rows | suggests, may, one study reported | is known to, clearly |
| Contested | A `conflicting` row is in the set | studies disagree, and both ids are cited | picking one side as fact |
| Background | `background` rows only | definitions and scope | empirical results |
| None | No row | do not write the sentence; leave `[NEEDS SOURCE]` | any factual claim |

A `cross-sectional` row does not support `causes` or `leads to`. If `study_design` is empty, write `is associated with` and `[VERIFY design]`, then resolve it before the checker will pass.

5. Citation keys, in the prose only, use one of these shapes. The year and the family name come from the evidence row. `et al.` is for three or more authors; two authors use `and`; one author stands alone. If the row does not list authors, stop and ask. Do not shorten a name to force the pattern.

```
(Smith et al., 2020; E014)
(Smith and Lee, 2020; E014)
(Smith, 2020; E014)
(Smith et al., 2020; E014; Lee, 2021; E015)
```

Every ID in the header appears at least once in the prose, and the prose cites no other ID. A figure mention (`Fig. 1`) must be an id in the ledger. Do not write "with permission" unless that ledger row is `granted`.

6. Keep the prose within 10 percent of the outline word budget. If it cannot be done without cutting a cited result, stop and ask the user to reopen the outline lock. Do not silently change the budget.
7. Run:

```
python3 <suite>/skills/review-section-drafter/scripts/check_citations.py \
  <project>/09-draft/S02-shared-findings.md \
  --budget 1800 \
  --evidence <project>/evidence/evidence_table.csv
```

Use the real path and the real budget. `[NEEDS SOURCE]` and `[VERIFY]` fail the command on purpose. Replace the path and budget for the section you drafted.

8. Set `Status: draft` to `Status: checked` only when the command prints `OK citations`. Append:

`YYYY-MM-DD | review-section-drafter | drafted S2 | agent`

9. Show the section to the user. Start the next outline section only if the user does not object. If any marker remains, do not continue.

## Human gate(s)

No project-level lock. Stop when the checker reports `[NEEDS SOURCE]`, `[VERIFY]`, an unknown ID, or a word count outside the 10 percent band. The user decides whether to reopen the outline or drop the sentence.

## Outputs (exact paths + formats)

- `<project>/09-draft/S0N-title-slug.md` — header bullets plus `## Prose`. One section per file.

Examples of the ladder and of a full paragraph are in `references/claim_strength.md` and `references/paragraph_and_citations.md`.

## Quality checklist

- The checker prints `OK citations` for this file.
- Header IDs and prose IDs are the same set.
- No paragraph states a result from one study as if several studies agreed.
- Causal verbs appear only when the row's design supports them.
- The file does not contain a DOI, PMID, page number, or sample size that is not in the evidence row or its reading note.

## Guardrails

- Model knowledge is not a source. If you cannot point to a row, the sentence is `[NEEDS SOURCE]` or it is deleted.
- Do not quote more than a short phrase, and only when the reading note already records the page. Do not paste abstracts.
- Do not convert citations to a numbered journal style in this skill. That happens in `manuscript-polishing`.
- Do not draft the abstract, cover letter, or response to reviewers here.

## Next step

The next locked outline section, until every non-structural section has a checked file. Then `journal-selection`.
