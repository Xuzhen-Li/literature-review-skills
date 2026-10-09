# Dedup rules

`scripts/dedup.py` keeps the first record in file order and folds later copies into it.

## Normalization

- DOI: strip `https://doi.org/`, `http://dx.doi.org/`, and a leading `doi:`; lowercase; drop a trailing period or comma. `10.1000/ABC` and `HTTPS://DOI.ORG/10.1000/abc` are the same key.
- PMID: digits from a `PMID:` label, a `pubmed.ncbi.nlm.nih.gov/<digits>` URL, or a field that is only digits. A Web of Science accession (`WOS:...`) is not a PMID.
- Title: lowercase, punctuation becomes a space, repeated spaces collapse. `Hello, World!` and `Hello World` share a title key.
- Year: the first four-digit year from 1600 through 2099. `2020 Jan 15` yields `2020`.
- Title+year key exists only when both the normalized title and the year are non-empty.

## Priority

1. Equal normalized DOI: merge, even if the titles differ.
2. Else equal PMID, unless both records have DOIs and those DOIs differ.
3. Else equal title+year, unless both records have DOIs that differ or both have PMIDs that differ.

Two records with the same title and year but DOIs `10.9000/one` and `10.9000/two` stay as two rows.

## Counts

`duplicates_removed_by_key` counts which rule fired for each discarded copy. `n_copies` on the kept row includes the kept record. `sources` lists each database once, in the order first seen.

Empty exports fail the script (`no records parsed`) instead of writing a silent empty library.
