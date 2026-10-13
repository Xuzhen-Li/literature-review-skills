---
name: review-figures-and-tables
description: >
  Plans original figures and synthesis tables for a review and records each
  item as original, adapted, or reused. Use when the user says "figure plan",
  "Fig. 1", "synthesis table", "comparison matrix", "figure ledger", or
  "permission status", "draw the original figures", or "crop a panel".
  Do not use to download a PDF. Crop only a local PDF already in the
  project, and only through the crop ledger. Permission requests belong
  to figure-permissions.
---

# Review figures and tables

## Opening

On first use in a project, say this verbatim:

I am review figures and tables. Original drawings stay SVG and PDF, and a published panel is cropped only from a PDF you already have, with a crop ledger.

## When to use

The outline is locked. You are deciding what art and tables the review will contain, then drawing each original item as an editable SVG plus a PDF. A published panel may be cropped only from a PDF the user already has, with one row in `panel_crop_ledger.csv`. Adapted and reused items that are not cropped here stay in the figure ledger for `figure-permissions`.

## Inputs (paths) / Preconditions

- `<project>/07-outline/outline.md` with `Status: locked`. If it is still `draft`, stop and return to `review-outline-builder`.
- `<project>/evidence/evidence_table.csv`
- `<project>/05-reading/` notes, including any quotable figure ideas already recorded there.
- `shared/writing_rules.md`

`<suite>` is this skill's suite directory. `<project>` is the review folder.

## Procedure (numbered steps)

1. Read every `Figures/tables` bullet in the outline. Add `Fig. 1` if the outline forgot it. Fig. 1 is an original conceptual overview of this review's argument. It is not a redraw of a published graphical abstract.
2. Create `<project>/08-figures/figure_plan.md`. Give each item a heading (`## Fig. 1`, `## Table 1`, `## Box 1`) and these bullets:
   - `Message:` one sentence the reader should remember.
   - `Type:` `original`, `adapted`, or `reused`.
   - `Evidence IDs:` IDs that justify the content. For original items this is the evidence the drawing is based on, not a source being copied.
   - `Panels or columns:` what each panel or column shows, in words.
   - `Do not copy:` the published figure or table, if any, that this item must not reproduce. Write `none` only when you are not looking at a published graphic.
   - `File:` the later image or table filename, or `not drawn yet`.
3. Prefer original schematics and synthesis tables. A synthesis table compares evidence rows in columns you define (study, design, population, finding, limitation). It does not paste a published table.
4. Classify before you describe the graphic:
   - `original` — you are not reproducing someone else's arrangement, artwork, or table layout. Facts and methods may be restated. Copyright protects expression, not the underlying facts (https://www.copyright.gov/circs/circ01.pdf).
   - `adapted` — a reader would recognize the source graphic, including a close redraw.
   - `reused` — the published image or table would be inserted.
5. Write `<project>/08-figures/figure_ledger.csv` with this header:

```
id,type,sources,license,permission_status,caption_credit
```

Optional columns, only if you have them: `title`, `license_url`, `notes`.

Controlled values:

| Column | Allowed values |
| --- | --- |
| id | `Fig. 1`, `Fig. 2`, `Table 1`, `Box 1` (optional panel letter, as in `Fig. 2a`) |
| type | `original`, `adapted`, `reused` |
| sources | `none` for original; otherwise include an evidence ID (`E014`) plus the figure or table number in that paper |
| license | `original`, `cc-by`, `cc-by-sa`, `cc-by-nc`, `cc-by-nc-sa`, `cc-by-nd`, `cc-by-nc-nd`, `cc0`, `public-domain`, `publisher-owned`, `own-previous`, `unknown` |
| permission_status | `not_required`, `needed`, `requested`, `granted` |
| caption_credit | `Created for this review.` / `Reproduced from ...` / `Adapted from ...` / `PENDING` |

6. License rules for the ledger:
   - Read the license on the version-of-record HTML page. If you have not opened that page, the license is `unknown`, the status is `needed`, and the credit is `PENDING`. Do not guess `cc-by` because the journal is open access.
   - `own-previous` means you have not yet classified the old paper's version-of-record license. Leave it `needed` / `PENDING` until you do. Your own copyright transfer does not make the figure free to reuse.
   - `cc-by`, `cc0`, and `public-domain` may use `not_required` once the credit line is final. `cc-by-nd` may use `not_required` only for unmodified `reused` items.
   - Every other resolved license uses `needed`, `requested`, or `granted`. `granted` requires a final credit line, not `PENDING`.
   - `license_url`, when present, is the Creative Commons deed you opened (https://creativecommons.org/licenses/) or the publisher page. No shadow-library URLs.
7. Examples that pass the checker are in `references/figure_ledger_example.csv` and `references/figure_ledger_adapted_example.csv`. Replace the sample `E010` and the sample citation. Do not ship those names.
8. Run:

```
python3 <suite>/skills/review-figures-and-tables/scripts/validate_ledger.py \
  <project>/08-figures/figure_ledger.csv \
  --evidence <project>/evidence/evidence_table.csv
```

`--strict` is for later, at submission. Do not use it while a row is still `needed`.

9. Draw every `original` item. The script writes `08-figures/fig-1.svg` and `fig-1.pdf` (and `table-1`, `box-1`, and panel letters the same way). Fig. 1 is an argument map. Tables and boxes are column schematics, not copied cells. Adapted and reused rows are skipped. `draw_originals.py` still refuses a message that asks it to crop. Cropping is the next step, not this command.

```
python3 <suite>/skills/review-figures-and-tables/scripts/draw_originals.py \
  --plan <project>/08-figures/figure_plan.md \
  --ledger <project>/08-figures/figure_ledger.csv \
  --out <project>/08-figures
```

The command must print `OK originals`. Then set each original item's `File:` bullet to its `.svg` path. Evidence IDs from the plan are written into the SVG and the PDF.

10. Crop a published panel only when the user already has the PDF. Write `08-figures/panel_crop_ledger.csv` with this header:

```text
figure_id,panel_id,source_pdf,page,original_figure,crop_box,copyright_status,used_in
```

`source_pdf` is a local path. `crop_box` is `x0,y0,x1,y1` in PDF points. `copyright_status` is `cc-by`, `cc-by-nc`, `publisher-permission-granted`, or `needs-permission`. The same source PDF, page, original figure, and crop box cannot appear twice. An empty or missing ledger writes nothing. `needs-permission` is not a publication file until `figure-permissions` changes that status. Do not download the PDF.

```bash
python3 <suite>/skills/review-figures-and-tables/scripts/crop_panels.py \
  --ledger <project>/08-figures/panel_crop_ledger.csv \
  --out <project>/08-figures/crops
```

`OK panel crops` is required before those files are cited. If `crop_blocked.tsv` exists, submission waits.

11. If any row is `adapted` or `reused`, or any crop row is `needs-permission`, show the user the row and ask whether to pursue permission or replace it with an original. Record the answer in `LOG.md`:

`YYYY-MM-DD | review-figures-and-tables | Fig. 2 will be requested or replaced | human`

12. Append a one-line decision for the plan itself:

`YYYY-MM-DD | review-figures-and-tables | figure plan written, N items | agent`

## Human gate(s)

No project-level lock. Stop and ask when any ledger row is `adapted` or `reused`, or any crop row is `needs-permission`, because that commits the user to a permissions request or a replacement. Do not tell the user a publisher has granted permission.

## Outputs (exact paths + formats)

- `<project>/08-figures/figure_plan.md` — one section per item, bullets listed above.
- `<project>/08-figures/figure_ledger.csv` — header and values in step 5.
- `<project>/08-figures/<slug>.svg` and `<slug>.pdf` for each original item (`Fig. 1` is `fig-1`).
- `<project>/08-figures/panel_crop_ledger.csv` and `08-figures/crops/` when a published panel is cropped.

## Quality checklist

- `validate_ledger.py` prints `OK ledger` and `draw_originals.py` prints `OK originals`.
- `Fig. 1` exists, is `original`, and its SVG says `argument map`.
- Every plan heading has one ledger row, and every ledger id has a plan section.
- Every original ledger row has an SVG and a PDF that contain that item's evidence IDs.
- No row cites a paper that is missing from the evidence table. Add the paper through `paper-deep-reading` first; do not invent a row.
- Caption credits do not say "with permission" unless `permission_status` is `granted`.
- A cropped file exists only when `crop_panels.py` printed `OK panel crops` for a ledger whose source PDFs are local. No file was downloaded from a search engine or a shadow library.

## Guardrails

- Do not download a paper to crop it. The source PDF must already be on disk.
- Do not crop the same source panel into two files.
- Do not paste a published figure into the project, or trace it, outside `crop_panels.py` and the ledger.
- Do not set `license` to a Creative Commons code you did not read on the version of record.
- Do not write `Reproduced from` or `Adapted from` until the source citation and the license are both known. Until then the credit cell is `PENDING`.
- Do not send permission email in this skill.

## Next step

`review-section-drafter`. If any row is `adapted` or `reused`, also open `figure-permissions` now so the request is not left until submission.
