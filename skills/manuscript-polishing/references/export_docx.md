# Docx export

Prefer pandoc. Official manual: https://pandoc.org/MANUAL.html. Install instructions, if the user chooses to install it: https://pandoc.org/installing.html.

```
pandoc "<project>/10-polish/manuscript.md" \
  --from=markdown \
  --to=docx \
  --output="<project>/10-polish/manuscript_polished.docx"
```

The same command with `--reference-doc` is in `SKILL.md`. Use a reference docx only when the user already has the journal's file.

## python-docx fallback

Use this only when pandoc is missing and the user runs it. Do not install packages yourself. The library is documented at https://python-docx.readthedocs.io/en/latest/.

```
python3 -c "import docx"
```

If that fails, stop. If it succeeds, the user can run a short script they save as `<project>/10-polish/export_docx.py`:

```python
from pathlib import Path
import docx

source = Path("10-polish/manuscript.md").read_text(encoding="utf-8")
document = docx.Document()
for block in source.split("\n\n"):
    document.add_paragraph(block.replace("**", "").replace("## ", ""))
document.save("10-polish/manuscript_polished.docx")
```

That fallback keeps paragraphs and strips a little markdown. It does not apply a journal template. Say so in `LOG.md`. The response letter uses the same pandoc command with the paths in `reviewer-response`.
