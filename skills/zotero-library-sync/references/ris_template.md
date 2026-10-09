# RIS record

One record per included paper. Omit a line when the value is empty. `ER` closes the record. Authors: one `AU` line per author, split from `library.csv` on `; `.

```text
TY  - JOUR
TI  - Title as stored
AU  - Family, Given
PY  - 2020
JO  - Journal title
DO  - 10.xxxx/xxxxx
AN  - 12345678
AB  - Abstract text if present
N1  - record_id R0001
ER  -
```

`DO` is the normalized DOI from the library. `AN` is the PMID digits only. `N1` keeps the library `record_id` so a later import can be checked. Do not put a guessed DOI in `DO`.
