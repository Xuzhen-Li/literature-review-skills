"""Tests for locked search strings and optional breadths."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from check_strings import check_strings, main  # noqa: E402


def test_one_locked_string_or_three_breadths():
    single = """## PubMed

```
grape[tiab]
```

- Locked: yes

## PRISMA-S

16. Deduplication: later
"""
    assert check_strings(single) == []
    two_db = single + """
## Scopus

```
TITLE-ABS-KEY(grape)
```

- Locked: yes
"""
    assert check_strings(two_db) == []
    triple = """## Scopus

### wide

```
TITLE-ABS-KEY(grape)
```

- Locked: no

### middle

```
TITLE-ABS-KEY(grape AND aroma)
```

- Locked: yes

### tight

```
TITLE-ABS-KEY(grape AND aroma AND linalool)
```

- Locked: no
"""
    assert check_strings(triple) == []
    two_locks = triple.replace("- Locked: no", "- Locked: yes", 1)
    assert any("exactly one" in error for error in check_strings(two_locks))
    missing_middle = triple.replace("### middle\n", "### other\n")
    assert any("together" in error for error in check_strings(missing_middle))


def test_cli_and_declined_breadth(tmp_path):
    declined = """## PubMed

```
grape[tiab]
```

- Locked: yes
- Breadth declined: the user will screen the pasted count
"""
    path = tmp_path / "search_strings.md"
    path.write_text(declined, encoding="utf-8")
    assert main([str(path)]) == 0
    both = declined + "\n### wide\n\n```\nx\n```\n"
    path.write_text(both, encoding="utf-8")
    assert main([str(path)]) == 1
