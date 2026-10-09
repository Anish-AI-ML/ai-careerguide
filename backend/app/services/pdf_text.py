import io
from pypdf import PdfReader

MAX_PAGES = 10
MAX_CHARS = 60_000


class PdfError(ValueError):
    pass


def extract_pdf_text(data: bytes) -> str:
    try:
        reader = PdfReader(io.BytesIO(data))
        if reader.is_encrypted:
            raise PdfError("This PDF is password-protected. Remove the password and try again.")
        if len(reader.pages) > MAX_PAGES:
            raise PdfError(f"This PDF has {len(reader.pages)} pages; resumes should be at most {MAX_PAGES}.")
        text = "\n".join((p.extract_text() or "") for p in reader.pages)
    except PdfError:
        raise
    except Exception:
        raise PdfError("Could not read this PDF. It may be corrupted.")
    text = text.replace("\x00", "").strip()
    if len(text) < 80:
        raise PdfError("Could not find readable text. Scanned or image-only PDFs are not supported; export a text-based PDF instead.")
    return text[:MAX_CHARS]
