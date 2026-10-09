# Eligibility criteria

Locked question: [paste from 00-scope/scope_report.md]

Review type: [narrative|systematic|scoping|umbrella]

A record must meet every include rule and no exclude rule. Rules below are starters. Delete a row that the locked question does not need, and add a row the user asked for. Do not invent a population.

## Include

| ID | Rule | Notes |
|----|------|-------|
| IN1 | The record addresses the locked question's population or system. | |
| IN2 | The record addresses the locked concept, intervention, or exposure. | |
| IN3 | The record reports the outcome or phenomenon named in the scope. | Narrative reviews may narrow this; write the narrower rule here. |
| IN4 | The publication type is allowed. | For an umbrella review, IN4 is "the record is a systematic or scoping review". |

## Exclude

| reason_code | Rule | Stage |
|-------------|------|-------|
| TA_OFF_TOPIC | Title and abstract show the paper is outside the locked question. | title_abstract |
| TA_WRONG_TYPE | Publication type is not allowed (editorial, news, conference abstract) if IN4 says so. | title_abstract |
| TA_WRONG_POPULATION | Wrong population, species, or setting. | title_abstract |
| TA_WRONG_DATE | Outside a date limit that was justified in the search file. | title_abstract |
| TA_LANGUAGE | Language limit that was justified in the search file. | title_abstract |
| FT_WRONG_DESIGN | Full text shows a design the criteria do not allow. | full_text |
| FT_NO_OUTCOME | Full text does not report the outcome or phenomenon. | full_text |
| FT_DUPLICATE_REPORT | Same study already included under another record_id. Keep the most complete report and name the kept id in reason_note. | full_text |
| FT_OTHER | Use only with a one-sentence reason_note. | full_text |
| FT_NOT_RETRIEVED | Full text could not be obtained by a legal route. This is a retrieval failure, not an eligibility exclusion. | full_text |

## Consensus

Two screeners: both must record a decision before `consensus` is filled. Disagreements are discussed against these rules, not against a new rule invented during the discussion. If the discussion needs a new rule, clear `inclusion_lock`, edit this file, and ask the user to lock it again.
