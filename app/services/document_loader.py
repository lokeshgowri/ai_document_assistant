import logging
from pathlib import Path

from docx import Document
from pypdf import PdfReader

from app.exceptions import DocumentProcessingError


logger = logging.getLogger(__name__)


SUPPORTED_EXTENSIONS = {".txt", ".pdf", ".docx"}


def load_document(file_path: str) -> dict:
    """
    Load a TXT, PDF, or DOCX document and return its text and source.
    """

    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"Document not found: {file_path}")

    if path.suffix.lower() not in SUPPORTED_EXTENSIONS:
        raise ValueError(
            f"Unsupported document type: {path.suffix}"
        )

    try:
        if path.suffix.lower() == ".txt":
            text = _load_txt(path)

        elif path.suffix.lower() == ".pdf":
            text = _load_pdf(path)

        else:
            text = _load_docx(path)

        logger.info("Successfully loaded document: %s", path.name)

        return {
            "text": text,
            "source": path.name,
        }

    except Exception as exc:
        logger.exception("Failed to process document: %s", path.name)

        raise DocumentProcessingError(
            f"Failed to process document: {path.name}"
        ) from exc


def _load_txt(path: Path) -> str:
    with path.open("r", encoding="utf-8") as file:
        return file.read()


def _load_pdf(path: Path) -> str:
    reader = PdfReader(str(path))

    pages = []

    for page in reader.pages:
        page_text = page.extract_text()

        if page_text:
            pages.append(page_text)

    return "\n".join(pages)


def _load_docx(path: Path) -> str:
    document = Document(str(path))

    paragraphs = []

    for paragraph in document.paragraphs:
        if paragraph.text.strip():
            paragraphs.append(paragraph.text)

    return "\n".join(paragraphs)