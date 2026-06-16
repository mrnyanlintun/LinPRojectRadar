"""
lin-project-radar backend — rag.py  (Sprint 0 item 23)
Technical Auditor RAG: chunk a corpus PDF by MasterFormat section, then do
simple keyword retrieval of the most relevant sections for an audit.
"""
import io
import re

try:
    import pypdf
except Exception:  # pragma: no cover - pypdf optional at import time
    pypdf = None

SECTION_RE = re.compile(r"(SECTION\s+\d{2}\s+\d{2}\s+\d{2}[\s\w\-]*)", re.IGNORECASE)


def detect_sections(text: str) -> list:
    """Return the list of distinct MasterFormat section headings in `text`."""
    if not text:
        return []
    seen, out = set(), []
    for m in SECTION_RE.findall(text):
        s = re.sub(r"\s+", " ", m).strip()[:60]
        key = (re.search(r"SECTION\s+\d{2}\s+\d{2}\s+\d{2}", s, re.IGNORECASE) or [s])[0].upper()
        if key not in seen:
            seen.add(key)
            out.append(s)
    return out


def build_requirements_db(pdf_bytes: bytes, doc_type: str) -> dict:
    """Extract and chunk a corpus PDF by MasterFormat section."""
    if pypdf is None:
        return {}
    reader = pypdf.PdfReader(io.BytesIO(pdf_bytes))
    db = {}
    current_section = "General"
    for page_num, page in enumerate(reader.pages):
        text = page.extract_text() or ""
        section_match = SECTION_RE.search(text)
        if section_match:
            current_section = section_match.group(0).strip()
        db.setdefault(current_section, []).append({
            "page": page_num + 1,
            "content": text.strip(),
            "docType": doc_type,
        })
    return db


def retrieve_relevant_chunks(requirements_db: dict, submittal_text: str, max_chunks: int = 3) -> str:
    """Simple keyword retrieval — find the most relevant spec sections."""
    query_words = set((submittal_text or "").lower().split())
    scored = []
    for section, chunks in requirements_db.items():
        section_text = " ".join(c.get("content", "") for c in chunks)
        score = len(query_words & set(section_text.lower().split()))
        scored.append((score, section, chunks))
    scored.sort(key=lambda t: t[0], reverse=True)

    result = ""
    for score, section, chunks in scored[:max_chunks]:
        if score > 0 and chunks:
            result += f"\n\n--- {section} ---\n"
            result += chunks[0].get("content", "")[:2000]
    return result
