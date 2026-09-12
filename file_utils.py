"""Plain-text extraction helpers for uploaded CV files.

No chunking, no embeddings, no vector index — the full extracted text is
passed straight into the LLM prompt for the current session only.
"""
import io


def extract_text_from_upload(uploaded_file):
    """Return plain text from a Streamlit UploadedFile (pdf, docx, or txt)."""
    if uploaded_file is None:
        return ""
    name = uploaded_file.name.lower()
    data = uploaded_file.getvalue()

    if name.endswith(".pdf"):
        return _extract_pdf(data)
    if name.endswith(".docx"):
        return _extract_docx(data)
    # fall back to treating it as plain text
    try:
        return data.decode("utf-8", errors="ignore")
    except Exception:
        return ""


def _extract_pdf(data: bytes) -> str:
    try:
        from pypdf import PdfReader
    except ImportError:
        return "[Could not extract PDF text — pypdf is not installed.]"
    try:
        reader = PdfReader(io.BytesIO(data))
        pages = [page.extract_text() or "" for page in reader.pages]
        return "\n".join(pages).strip()
    except Exception as e:
        return f"[Could not extract PDF text: {e}]"


def _extract_docx(data: bytes) -> str:
    try:
        import docx
    except ImportError:
        return "[Could not extract DOCX text — python-docx is not installed.]"
    try:
        document = docx.Document(io.BytesIO(data))
        paragraphs = [p.text for p in document.paragraphs]
        return "\n".join(paragraphs).strip()
    except Exception as e:
        return f"[Could not extract DOCX text: {e}]"
