"""
Read a .docx into text and tables, locally, before anything is sent to the model.

WHY A DOCX IS NOT SENT AS A DOCUMENT BLOCK

`extraction_client._content_block` sends a PDF to the model as a `document` block and decodes
anything else as UTF-8 text. A .docx is a ZIP archive, so that second branch produced 12000
characters of deflate-compressed binary: measured on a real file, 5071 U+FFFD replacement
characters, and the 12000-character truncation was consumed by ZIP local-file headers before the
document body was reached at all. The model was being shown archive structure, never prose.

Reading it here is the better route for these documents rather than a workaround for that bug:

  - The tables survive AS TABLES. A pay application carries its figures in a grid whose meaning
    is positional — the number 4,182,500 means nothing without the column head "Total Completed
    and Stored to Date" above it and the row label "Grand Total" beside it. A document block asks
    the model to recover that grid from rendered layout; reading the XML gives it the grid the
    author actually wrote.
  - There is no OCR step and no rasterisation, so nothing depends on how a page happened to lay
    out.
  - It costs no new dependency. `python-docx` is not in `server/requirements.txt` and is not in
    the server virtualenv; WordprocessingML is XML inside a ZIP and both are stdlib. That matches
    the standing reason `extraction_client` uses `urllib` rather than the anthropic SDK: this
    build has been bitten twice by interpreter-specific wheels and the pinned requirements are
    deliberately small.

WHAT IS DELIBERATELY NOT DONE

No styling, no numbering resolution, no images, no revision-history flattening. The extraction
fields are figures and dates that appear in body text and summary tables. Reconstructing a list's
computed numbering, or rendering a chart, would add surface without adding a field the platform
asks for.
"""
from __future__ import annotations

import xml.etree.ElementTree as ET
import zipfile
from io import BytesIO

W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"

DOCX_MIME = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"

# The ZIP member holding the body. `word/document.xml` is fixed by the OPC part naming for a
# WordprocessingML main document part; it is not discovered from the relationships graph because
# every producer that writes this format writes that name.
_MAIN_PART = "word/document.xml"

# Generous, and much larger than the 12000-character cap the raw-bytes text branch applies.
# That cap exists to bound a prompt built from an unknown blob; this text is a document the
# platform has already parsed, and a pay application's continuation sheet alone can run past
# 12000 characters before the summary rows are reached. Truncating there would drop exactly the
# totals the extraction wants. ~60000 characters is roughly 15k tokens, well inside the model's
# window and still a hard bound against a pathological file.
DOCX_TEXT_LIMIT = 60000

# Said out loud in the prompt text when the bound is hit, so a short extraction can be traced to
# a truncated document rather than to a model that missed a field. Never silent.
TRUNCATION_NOTE = "\n\n[DOCUMENT TRUNCATED: it is longer than this reader sends to the model.]"


class DocxReadError(RuntimeError):
    """Raised when the bytes are not a readable .docx. Never returns partial text instead."""


def is_docx(raw: bytes, mime_type: str = "", filename: str = "") -> bool:
    """
    Decide from the BYTES first, and fall back to the declared type and the extension.

    The bytes are authoritative because a browser's `file.type` is unreliable: `signals.js` sends
    `file.type || "application/pdf"`, so a docx whose type the browser did not resolve arrives
    claiming to be a PDF. Sniffing the archive is what stops that from being sent as a document
    block.
    """
    if raw[:2] == b"PK":
        try:
            with zipfile.ZipFile(BytesIO(raw)) as zf:
                return _MAIN_PART in zf.namelist()
        except (zipfile.BadZipFile, OSError):
            return False
    if (mime_type or "").lower() == DOCX_MIME:
        return True
    return (filename or "").lower().endswith(".docx")


def _cell_text(tc: ET.Element) -> str:
    """One cell flattened to a single line, because a row must stay on one line to read as a row."""
    parts = [_para_text(p) for p in tc.iter(f"{W}p")]
    return " ".join(part for part in (s.strip() for s in parts) if part)


def _para_text(p: ET.Element) -> str:
    """
    One paragraph's visible text, in document order.

    Only `w:t`, `w:tab` and the break elements carry visible content. Iterating the element tree
    rather than reading `itertext()` keeps deleted text (`w:delText`, inside a tracked deletion)
    out: that text is not in the document as it stands, and a superseded figure reading as
    current is exactly the failure this platform refuses elsewhere.
    """
    out: list[str] = []
    for node in p.iter():
        tag = node.tag
        if tag == f"{W}t":
            out.append(node.text or "")
        elif tag == f"{W}tab":
            out.append("\t")
        elif tag in (f"{W}br", f"{W}cr"):
            out.append(" ")
    return "".join(out)


def _row_cells(tr: ET.Element) -> list[str]:
    """
    A row's cells, with horizontal merges expanded so every row has the same column count.

    A `w:gridSpan` of 3 is ONE `w:tc` occupying three grid columns. Emitting it as a single cell
    shifts every later cell in that row left relative to the header, which silently re-labels the
    figures. The value is emitted once and the spanned remainder is padded, so column position is
    preserved. `w:vMerge` continuation cells carry no text of their own and come out empty, which
    is what they are.
    """
    cells: list[str] = []
    for tc in tr.findall(f"{W}tc"):
        span = 1
        pr = tc.find(f"{W}tcPr")
        if pr is not None:
            gs = pr.find(f"{W}gridSpan")
            if gs is not None:
                try:
                    span = max(1, int(gs.get(f"{W}val") or "1"))
                except ValueError:
                    span = 1
        cells.append(_cell_text(tc))
        cells.extend([""] * (span - 1))
    return cells


def _table_text(tbl: ET.Element) -> str:
    """
    Render one table as a pipe-delimited grid with its header row marked.

    THE FORMAT IS THE POINT. A flat run of numbers loses which column a figure sat under, and the
    brief for this work is explicit that a pay application read that way will not extract
    correctly. A pipe grid keeps three things the figures depend on: the column heads, the row
    labels, and the alignment between them. It is also a format the model reads natively, so no
    instruction has to explain it.

    The first row is treated as the header. That is a convention, not a fact about the document,
    and it is stated in the prompt rather than relied on silently: a table whose first row is not
    a header still renders every cell in position, so nothing is lost when the convention does
    not hold.
    """
    # Direct children only. A nested table's rows belong to the nested table, and `iter` would
    # hoist them into the outer one with the wrong column count.
    rows = [_row_cells(tr) for tr in tbl.findall(f"{W}tr")]
    rows = [r for r in rows if any(c.strip() for c in r)]
    if not rows:
        return ""
    width = max(len(r) for r in rows)
    padded = [r + [""] * (width - len(r)) for r in rows]

    def line(cells: list[str]) -> str:
        return "| " + " | ".join(c.replace("|", "\\|").strip() for c in cells) + " |"

    out = [line(padded[0]), "|" + "|".join([" --- "] * width) + "|"]
    out.extend(line(r) for r in padded[1:])
    return "\n".join(out)


def docx_to_text(raw: bytes) -> str:
    """
    The document as text, with tables rendered as grids, in document order.

    Body order is preserved by walking the direct children of `w:body` rather than collecting all
    paragraphs and then all tables: a figure's meaning often depends on the heading immediately
    above its table, and a reordered document puts that heading somewhere else.
    """
    try:
        with zipfile.ZipFile(BytesIO(raw)) as zf:
            xml = zf.read(_MAIN_PART)
    except KeyError:
        raise DocxReadError("not a Word document: the archive has no word/document.xml") from None
    except (zipfile.BadZipFile, OSError) as exc:
        raise DocxReadError(f"could not open the .docx archive: {exc}") from None

    try:
        root = ET.fromstring(xml)
    except ET.ParseError as exc:
        raise DocxReadError(f"word/document.xml is not parseable XML: {exc}") from None

    body = root.find(f"{W}body")
    if body is None:
        raise DocxReadError("word/document.xml has no body")

    blocks: list[str] = []
    for child in body:
        if child.tag == f"{W}p":
            text = _para_text(child).strip()
            if text:
                blocks.append(text)
        elif child.tag == f"{W}tbl":
            table = _table_text(child)
            if table:
                blocks.append(table)
    return "\n\n".join(blocks)


def docx_content_block(raw: bytes) -> dict:
    """
    The `text` content block for a .docx, bounded and labelled.

    Raises `DocxReadError` if the document cannot be read. It is NOT downgraded to the raw-bytes
    text branch on failure: that branch is what produced the binary mojibake this module exists to
    stop, and falling back to it would restore the defect precisely when the reader has just said
    the file is unreadable.
    """
    text = docx_to_text(raw)
    if not text.strip():
        raise DocxReadError("the .docx contains no readable text or tables")
    if len(text) > DOCX_TEXT_LIMIT:
        text = text[:DOCX_TEXT_LIMIT] + TRUNCATION_NOTE
    return {
        "type": "text",
        "text": (
            "DOCUMENT TEXT (read from a Word .docx; tables are rendered as pipe-delimited "
            "grids, and the first row of each grid is normally its column headers):\n" + text
        ),
    }
