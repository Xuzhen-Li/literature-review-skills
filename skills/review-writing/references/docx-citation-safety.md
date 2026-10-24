# Word and Zotero safety

## How a Zotero citation is stored

A Zotero citation in `word/document.xml` is a complex field:

```xml
<w:r><w:fldChar w:fldCharType="begin"/></w:r>
<w:r><w:instrText> ADDIN ZOTERO_ITEM CSL_CITATION {"citationID":"a1b2","properties":{...},"citationItems":[{"id":12,"uris":["http://zotero.org/users/123/items/ABCD1234"],"itemData":{...}}],"schema":"https://github.com/citation-style-language/schema/raw/master/csl-citation.json"} </w:instrText></w:r>
<w:r><w:fldChar w:fldCharType="separate"/></w:r>
<w:r><w:t>(Smith et al., 2020)</w:t></w:r>
<w:r><w:fldChar w:fldCharType="end"/></w:r>
```

The bibliography is one field with `ADDIN ZOTERO_BIBL {...} CSL_BIBLIOGRAPHY`. The JSON may be split across several `w:instrText` runs; join them before parsing. EndNote uses `ADDIN EN.CITE` with the same begin/separate/end structure.

## Rules for every edit

- Default to editing the .docx itself in `full-word` mode, after saving `<name>.orig.docx`.
- Keep styles, comments (`comments.xml` and the range markers), tables, images, and `word/_rels/document.xml.rels` relationships.
- Move a citation by moving all runs from `begin` to `end` together. Never retype the visible text `(Smith et al., 2020)` as plain text; that kills the field.
- Keep `citationItems`, `itemData`, `uris`, and item ids unchanged. To change which source is cited, the author does it in Zotero, or you copy an existing field for that item.
- When a field is duplicated (the same source reused), give the copy a new unique `citationID` (any new short random string); Zotero treats duplicate IDs as one citation.
- When a paragraph is deleted, its citation fields go with it. Log any source that is now uncited; the bibliography updates on the next Refresh.
- Every `begin` has one `separate` and one `end`, in that order, without nesting errors.
- Every source cited in text appears in the bibliography and vice versa (after Refresh). Report mismatches.
- After editing, the visible citation text may be stale. Say that the author must click Zotero → Refresh in Word. Do not claim a Refresh you did not run, and do not claim the Zotero library was changed.
- Year, volume, issue, or author-case errors in the bibliography come from the Zotero database: list them for the author.

## Safe editing tools

- Preferred: python-docx for paragraph-level moves plus lxml on the paragraph XML, copying whole runs. Edit text only in `w:t` runs outside fields.
- Unsafe: round-tripping through pandoc, LibreOffice "save as .docx", Google Docs, or any converter that rewrites fields. Use LibreOffice only to render a PDF copy, never to save the deliverable.
- If you cannot keep the fields live (no XML access, a converter is the only route, or the check fails after editing and cannot be fixed), stop changing the original. Deliver revised text plus a replacement map: `| location | original paragraph (first words) | revised paragraph | citations to keep, in order |`, so the author pastes the text and reinserts or keeps fields in Word.

## Field check script

```bash
python3 <suite>/skills/review-writing/scripts/verify_docx_fields.py manuscript.docx
python3 <suite>/skills/review-writing/scripts/verify_docx_fields.py revised.docx --baseline manuscript.orig.docx
python3 <suite>/skills/review-writing/scripts/verify_docx_fields.py revised.docx --json
```

It reports: field begin/separate/end balance; counts of CSL_CITATION, CSL_BIBLIOGRAPHY, and EndNote fields; duplicate citationIDs; CSL JSON that does not parse; citations that look flattened to plain text (`(Name et al., 2020)` outside any field in a document that has Zotero fields); HTML escapes or tags in the bibliography; figure and table caption numbers versus in-text mentions; placeholders. With `--baseline` it also reports citation fields lost relative to the original. Exit code 1 means `FAIL`.

It does not check that a citation supports its sentence, and it cannot run a Zotero Refresh.

## Page rendering

```bash
mkdir -p qc
soffice --headless --convert-to pdf --outdir qc revised.docx
pdftoppm -r 80 -png qc/revised.pdf qc/page
ls qc/page-*.png | wc -l    # must equal the PDF page count (pdfinfo qc/revised.pdf)
```

Open every page image. Look for blank pages, clipped text, font fallback, blurred images, tables broken across pages, headings stranded at a page bottom, and figures separated from captions. LibreOffice layout can differ slightly from Word; note this, and ask the author to confirm pagination in Word if it matters. Keep `qc/` out of the submission folder.
