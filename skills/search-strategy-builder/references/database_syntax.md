# Database syntax

Confirm a tag on the live help page before the search lock if the interface disagrees with this sheet. The string that gets locked is the one the database history shows on a named date.

Official tag list for PubMed: https://pubmed.ncbi.nlm.nih.gov/help/search-tags/

PubMed proximity: https://pubmed.ncbi.nlm.nih.gov/help/proximity-search/

MeSH: https://www.ncbi.nlm.nih.gov/mesh/

## PubMed

| Tag | Field |
|-----|--------|
| `[ti]` | Title |
| `[tiab]` | Title/Abstract |
| `[tw]` | Text word |
| `[mh]` | MeSH, exploded |
| `[mh:noexp]` | MeSH, not exploded |
| `[majr]` | MeSH major topic |
| `[sh]` | MeSH subheading |
| `[pt]` | Publication type |
| `[au]` | Author |
| `[fau]` | Full author name |
| `[1au]` | First author |
| `[ta]` or `[jour]` | Journal |
| `[dp]` | Publication date |
| `[la]` | Language |
| `[ad]` | Affiliation |
| `[nm]` | Supplementary concept |
| `[gr]` | Grant number |
| `[lid]` | Location ID (DOI appears on some records) |

- `AND`, `OR`, `NOT` in uppercase. Group with parentheses.
- Phrases in double quotes. Truncation `*` needs at least four characters before the asterisk.
- Proximity: `"word1 word2"[tiab:~2]` means at most two words between the terms, in any order. Proximity applies to `[ti]`, `[tiab]`, and `[ad]` only.
- Date: `2018:2026[dp]`.
- A pasted DOI is recognized in the search box. Prefer `[tiab]`/`[mh]` blocks for the strategy, not a DOI list.
- After a run, copy History and Search Details from https://pubmed.ncbi.nlm.nih.gov/advanced/ so automatic term mapping is visible.

Illustrative only (do not reuse as a real strategy):

```text
("machine learning"[tiab] OR "deep learning"[tiab]) AND (diagnos*[tiab]) AND 2018:2026[dp]
```

## Web of Science Core Collection

Record which indexes were ticked (for example SCI-EXPANDED, SSCI). The same string changes count when the edition changes.

| Tag | Field |
|-----|--------|
| `TS=` | Topic (title, abstract, author keywords, Keywords Plus) |
| `TI=` | Title |
| `AB=` | Abstract |
| `AK=` | Author keywords |
| `KP=` | Keywords Plus |
| `AU=` | Author |
| `SO=` | Publication name |
| `DO=` | DOI |
| `PY=` | Year published |
| `AD=` | Address |
| `DT=` | Document type |
| `LA=` | Language |
| `WC=` | Web of Science category |
| `UT=` | Accession number |

- `AND`, `OR`, `NOT`. Proximity in topic fields is `NEAR/n` (unordered, n words). `SAME` is for addresses, not a general topic proximity operator.
- Wildcards: `*` (zero or more), `?` (one character), `$` (zero or one).
- Phrases in double quotes. Years: `PY=(2018-2026)`.
- PubMed ID: use the tag the advanced-search field list shows on the day you search. Write that tag in `search_strings.md`. Do not guess it.

Illustrative only:

```text
TS=("machine learning" OR "deep learning") AND TS=(diagnos*) AND PY=(2018-2026)
```

## Scopus

| Code | Field |
|------|--------|
| `TITLE-ABS-KEY()` | Title, abstract, keywords |
| `TITLE()` | Title |
| `ABS()` | Abstract |
| `KEY()` | Keywords (author keywords, index terms, trade names, and chemical names) |
| `AUTH()` | Author (last name and first name) |
| `AUTHKEY()` | Author keywords only |
| `AU-ID()` | Scopus author id |
| `SRCTITLE()` | Source title |
| `DOI()` | DOI |
| `AFFIL()` | Affiliation |
| `INDEXTERMS()` | Index terms |
| `LANGUAGE()` | Language |
| `DOCTYPE()` | Document type |
| `SUBJAREA()` | Subject area |
| `PUBYEAR` | Year |
| `PMID()` | PubMed id, if the field list still shows it |

- `AND`, `OR`, `AND NOT`. Not the single word `NOT`.
- Double quotes are a loose phrase (stemming may still apply). Curly braces are the exact phrase: `{deep learning}`.
- Proximity: `W/n` any order, `PRE/n` preserved order.
- Wildcards `*` and `?` are literal inside braces.
- Years: `PUBYEAR > 2017 AND PUBYEAR < 2027`.
- Common document-type codes are `ar` (article) and `re` (review). Confirm the code list in Scopus before locking a `DOCTYPE()` limit.
- Scopus is not Embase. `INDEXTERMS()` is not a substitute for an Emtree explosion on Embase.com.

Illustrative only:

```text
TITLE-ABS-KEY("machine learning" OR "deep learning") AND TITLE-ABS-KEY(diagnos*) AND PUBYEAR > 2017 AND PUBYEAR < 2027
```

## Embase / Emtree (only if Embase is searched)

Label the platform in the strategy file.

- Embase.com: `'heart infarction'/exp` (exploded), `'heart infarction'/de` (not exploded), `:ti`, `:ab`, `:ti,ab`, `NEAR/n`, `NEXT/n`.
- Ovid Embase: `exp term/`, `term.ti,ab.`, `adj3`.

Do not paste either syntax into PubMed or Scopus.

## What to record for every database

Interface name, edition or indexes, date of the run, the exact string from the history panel, the hit count the user pasted, and any filter or limit with its reason.
