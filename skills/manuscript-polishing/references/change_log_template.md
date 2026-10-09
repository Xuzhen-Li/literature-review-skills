# Change log

Copy this header into `<project>/10-polish/change_log.csv`. Delete the example row before you run the checker. IDs must look like `C001`. `file` is always `10-polish/manuscript.md`. `location` contains `lines 12-14` or `p. 4, lines 88-92`.

```
id,file,location,change_type,before,after,reason
C001,10-polish/manuscript.md,lines 12-14,hedge,The data proves it,The data is consistent with it,E014 is a single cohort
```

`change_type` is one of: `hedge`, `language`, `consistency`, `citation`, `format`, `structure`, `cut_to_limit`.

`after` is `[deleted]` only when the type is `cut_to_limit` or `structure`. A reason that drops an evidence ID contains `dropped E014` with the real ID.
