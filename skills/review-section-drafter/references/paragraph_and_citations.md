# Paragraph and citation shapes

## Paragraph

One paragraph, four moves. The citation keys are inside the sentences that need them, not collected at the end.

> Two independent trials agree on the direction of the yield response, with a limitation the section claim has to keep. Both report a gain under the same irrigation regime (Ada et al., 2019; E010; Berg, 2021; E011). They differ in cultivar and in the size of the gain, and neither measured a third season. The section can therefore defend a directional claim for those two settings and not a general one.

If only E010 exists, delete the "both" sentence. Write what that one study reported and say it is a single study.

## Citation shapes the checker accepts

| Authors on the evidence row | Shape |
| --- | --- |
| 1 | `(Smith, 2020; E014)` |
| 2 | `(Smith and Lee, 2020; E014)` |
| 3 or more | `(Smith et al., 2020; E014)` |
| Two sources | `(Smith et al., 2020; E014; Lee, 2021; E015)` |

The year is four digits and matches the row. Do not use a numbered citation, a superscript, or a bare `E014`. Do not cite a paper that appears only in another paper's reference list. If the full text was never obtained, do not cite it.

`([VERIFY]; E014)` is a temporary marker. It is not a finished citation. The checker fails while it remains.

## What the checker does not do

It does not judge whether the science is true. It checks the key shape, that header IDs match the prose, that the words under `## Prose` are within 10 percent of `--budget`, and that `[NEEDS SOURCE]` and `[VERIFY]` are gone.
