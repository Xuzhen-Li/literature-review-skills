# Optional decision cards

A card may be shown before a lock. It is not a gate. The lock is still the exact sentence, the boolean in `project.yaml`, and the `LOG.md` line that ends with `| human`.

Use four labels. Mark one as preferred. If the user writes a custom option, restate it as a concrete plan and name the risks. Do not treat a card reply as a lock.

```text
Decision: <what the lock will record>
Preferred: A
A. <option> — preferred
B. <option>
C. <option>
D. Custom. Restate the user's words as a plan and list the risks.
Record: the exact sentence in shared/gates.md. The card is not the record.
```

The locks that may use a card are `topic_lock`, `search_lock`, `inclusion_lock`, `outline_lock`, `journal_lock`, and `final_submit`. `institutional_access` does not use a card.
