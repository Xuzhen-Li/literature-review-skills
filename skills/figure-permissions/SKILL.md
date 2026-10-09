---
name: figure-permissions
description: >
  Decides whether each reused or adapted figure needs attribution only, a
  ShareAlike check, a RightsLink request, or a replacement, and drafts the
  request for the user to send. Use when the user says "figure permission",
  "RightsLink", "CC BY", "credit line", "reproduced from", or "adapted from".
  Do not use for a figure you drew yourself, and do not click, pay, or email
  on the user's behalf.
---

# Figure permissions

## When to use

`08-figures/figure_ledger.csv` has at least one `adapted` or `reused` row. Original rows are not entered in the permissions log. Start this skill as soon as those rows exist. Do not wait until the week of submission.

## Inputs (paths) / Preconditions

- `<project>/08-figures/figure_ledger.csv` and `figure_plan.md`
- `<project>/evidence/evidence_table.csv` for the source papers
- The version-of-record HTML page of each source, which the user or the browser session opens. A PDF from an unknown site is not the license statement.
- `references/decision_tree.md`, `references/credit_lines.md`, `references/request_email.md`

This skill is not legal advice. The rights holder or the journal's permissions desk decides close calls.

## Procedure (numbered steps)

1. Skip every ledger row with `type` = `original`.
2. For each remaining row, open the version-of-record page and read the license line. Map it to one router value: `cc-by`, `cc-by-sa`, `cc-by-nc`, `cc-by-nc-sa`, `cc-by-nd`, `cc-by-nc-nd`, `cc0`, `public-domain`, `publisher-owned`, `own-previous`, or `unknown`. Deeds are linked from https://creativecommons.org/licenses/.
3. Run the router and paste the JSON `action` into the log:

```
python3 <suite>/skills/figure-permissions/scripts/route_permission.py reused cc-by
```

Replace `reused` and `cc-by` with the row's type and license. The action names and the rules are in `references/decision_tree.md`. Follow the script if it and your memory disagree; then fix the script only when the official license deed disagrees with the script.

4. Special cases the router already encodes, restated so you do not skip them:
   - `own-previous`: read the publishing agreement or the article's license. Then route again as `cc-by` or `publisher-owned` or whichever value the page supports. Do not assume that being an author restored the copyright.
   - `cc-by-nc` and `cc-by-nc-sa`: do not decide that a journal article is non-commercial. Request permission or replace the figure.
   - `cc-by-nd`: an adapted row is `do_not_adapt`. Replace it with an original that does not copy the expression, or the user requests a separate license.
   - `cc-by-sa`: stop until the user confirms the target journal can publish under ShareAlike. A copyright-transfer journal often cannot.
   - `publisher-owned`: the user starts at the permission button on the article page. When that button is RightsLink, the service is Copyright Clearance Center (https://www.copyright.com/). The user completes the form, pays if asked, and saves the receipt. You do not.
5. STM Permissions Guidelines are an agreement among signatory publishers, not a permission you can grant yourself. Read the current signatory list and the current quotas at https://stm-assoc.org/what-we-do/core-services/ip-copyright/permissions/permissions-guidelines/ on the day you need them. The 26 June 2024 update is linked from that page; use the page, not a remembered quota. Ask the target journal whether it will clear the item under those guidelines. File their written answer under `12-permissions/grants/`. Until that answer or a RightsLink receipt exists, the row stays ungranted.
6. Write `<project>/12-permissions/permissions_log.csv` with this header:

```
figure_id,source_citation,source_url,license,route_action,request_needed,request_date,grant_date,grant_reference,credit_line,blocker
```

`figure_id` is the ledger column `id` (`Fig. 2`), not a new name. `request_needed` is `yes` or `no` and must match the router's `request_needed`. An open request (`yes`, no grant date) needs a blocker note. A `do_not_adapt` row sets `credit_line` to `REMOVED` or `Replaced by Fig. N` and explains the blocker. `source_url` is https on the publisher's site. No shadow libraries.

7. For each row that needs a request, draft `<project>/12-permissions/emails/Fig-2.md` from `references/request_email.md`. Leave the send date blank. The user sends the email or submits the RightsLink form.
8. When the user reports a grant, store the PDF in `<project>/12-permissions/grants/` and fill `grant_date` and `grant_reference` from the receipt. Only then set the ledger `permission_status` to `granted` and replace `PENDING` with a credit line from `references/credit_lines.md`. `Reproduced from` is for `reused`. `Adapted from` is for `adapted`. Do not write "with permission" before the receipt is in the folder.
9. If the request is refused or the price is declined, change the figure plan to an original replacement or drop the item. Update the ledger. Do not leave a denied figure in the manuscript.
10. Run:

```
python3 <suite>/skills/figure-permissions/scripts/route_permission.py \
  --log <project>/12-permissions/permissions_log.csv
```

Then run `validate_ledger.py --strict` from `review-figures-and-tables` before submission. `--strict` fails while any reused or adapted row is still `needed`, `requested`, `unknown`, or `PENDING`.

11. Append `YYYY-MM-DD | figure-permissions | Fig. 2 granted or replaced | human` only after the user confirms the receipt or the replacement.

## Human gate(s)

The user sends every email, accepts every click-through license, and pays every fee. You stop at the draft email and at the RightsLink screen. You do not mark `granted` from an automated message you have not read.

## Outputs (exact paths + formats)

- `<project>/12-permissions/permissions_log.csv`
- `<project>/12-permissions/emails/Fig-N.md` for each request
- `<project>/12-permissions/grants/` — receipts and journal STM answers, added by the user
- Updated credit and status cells in `<project>/08-figures/figure_ledger.csv`

## Quality checklist

- The log checker prints `OK permissions log`.
- Every non-original ledger row has one log row, and the `route_action` is one of the names in `decision_tree.md`.
- No credit line says "with permission" without `grant_date` and `grant_reference`.
- CC BY and CC0 rows still name the source and the license URL.
- ND adaptations are `REMOVED` or replaced, not quietly cropped.

## Guardrails

- Do not download the figure from a shadow library "just to see the license".
- Do not treat a ResearchGate or author-posted PDF as the license.
- Do not invent a license number.
- Do not apply an STM quota yourself. Ask the journal, and quote only the quota and the signatory status you saw on the STM page that day.

## Next step

`submission-package` after `--strict` ledger validation passes. If a request is still open, submission waits.
