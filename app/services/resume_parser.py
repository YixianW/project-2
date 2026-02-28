from io import BytesIO

from docx import Document
from pypdf import PdfReader


def extract_resume_text(filename: str, raw_bytes: bytes) -> str:
    lower = filename.lower()
    if lower.endswith(".pdf"):
        reader = PdfReader(BytesIO(raw_bytes))
        return "\n".join((page.extract_text() or "") for page in reader.pages).strip()
    if lower.endswith(".docx"):
        doc = Document(BytesIO(raw_bytes))
        return "\n".join(p.text for p in doc.paragraphs).strip()
    raise ValueError("Unsupported file type. Upload PDF or DOCX.")
