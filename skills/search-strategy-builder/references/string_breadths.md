# Optional string breadths

Use one fenced string per database, marked `- Locked: yes`, unless the pasted hit count is extreme.

Extreme, in this suite, means the user says the count is too large or too small to screen, or the pasted integer is below 20 or above 5000. Those two bounds are suite defaults, not a database rule and not a published standard.

When the count is extreme, add three fenced strings under the same database heading:

```text
## PubMed

### wide

```
broad string
```

- Locked: no

### middle

```
middle string
```

- Locked: yes

### tight

```
tight string
```

- Locked: no
```

Exactly one of the three is `- Locked: yes`. That is the string `search-export-and-dedup` runs. The other two stay in the file so the choice is visible. Hit counts are still only numbers the user pasted. If a string was not run, its count is `[VERIFY]`, and a `[VERIFY]` count on the locked string still blocks `search_lock`.

If the user does not want three strings, keep the single locked string and add `- Breadth declined:` plus their reason. Do not invent a third count.
