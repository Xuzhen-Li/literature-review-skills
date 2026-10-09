# Systematic methods checklist

Copy this file to `07-outline/systematic_methods_checklist.md` when `review_type` is systematic. It is a reminder. It does not register a protocol, score bias, or calculate a pooled estimate.

## Protocol registration

PRISMA 2020 items 24a–24c ask for the register name and registration number, or a statement that the review was not registered; where the protocol can be accessed, or a statement that no protocol was prepared; and any amendments to either (https://www.prisma-statement.org/prisma-2020 and https://www.prisma-statement.org/prisma-2020-checklist).

PROSPERO registers systematic reviews that have a health-related outcome in humans, and the record has to be submitted before data extraction starts (https://www.crd.york.ac.uk/prospero/ and https://www.crd.york.ac.uk/PROSPERO/help/eligibility). It does not accept scoping reviews, or literature reviews that only ran a systematic search. Do not invent a PROSPERO ID. If this review is outside that scope, leave the ID as `none yet` and say in the methods that it was not registered there.

Registry ID: none yet
Registry source: not opened

A filled ID replaces that source line with `Registry source: verified on YYYY-MM-DD at https://...` for the register record you opened. The checker does not read a `Registry URL` line.

## Bias tool

These tools are not interchangeable. Name one only after you open its manual in this session, and do not fill a score from memory.

- RoB 2 assesses a result from a randomized trial (https://methods.cochrane.org/bias/resources/rob-2-revised-cochrane-risk-bias-tool-randomized-trials).
- ROBINS-I assesses a result from a non-randomized study of an intervention. Use the manual at https://www.riskofbias.info/, including the version that page marks as current.
- QUADAS-2 assesses risk of bias and applicability for a diagnostic accuracy study (patient selection, index test, reference standard, and flow and timing). Its developers now recommend QUADAS-3 for that job (https://www.bristol.ac.uk/population-health-sciences/projects/quadas/history/quadas-2/ and https://www.bristol.ac.uk/population-health-sciences/projects/quadas/).
- AMSTAR 2 appraises systematic reviews of healthcare interventions. It is not a risk-of-bias tool for a primary study (https://amstar.ca/).

Use RoB 2, ROBINS-I, or QUADAS-2 / QUADAS-3 on the primary studies that tool was built for. Use AMSTAR 2 only when the included records are themselves systematic reviews.

Tool: not chosen
Official page: not opened

A chosen tool sets `Official page:` to `verified on YYYY-MM-DD at https://...`.

## Pooled estimates

Pooling: out of scope
User asked: no

Leave quantitative pooling out unless the user asks for it and the outline says `- Pooled estimates: in scope` on its own line, with a section title that says so. This file does not compute one.
