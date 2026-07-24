from pathlib import Path
from docx import Document
import fitz


def load_job_from_text(text: str) -> dict:
    return {
        "source_type": "text",
        "filename": None,
        "text": text
    }


def load_job_from_txt(file_path: str) -> str:
    with open(file_path, "r", encoding="utf-8") as f:
        return f.read()


def load_job_from_docx(file_path: str) -> str:
    doc = Document(file_path)
    texts = [p.text for p in doc.paragraphs if p.text.strip()]
    return "\n".join(texts)


def load_job_from_pdf(file_path: str) -> str:
    doc = fitz.open(file_path)
    texts = [page.get_text("text") for page in doc]
    doc.close()
    return "\n".join(texts)


def load_job_file(file_path: str) -> dict:
    path = Path(file_path)
    suffix = path.suffix.lower()

    if suffix == ".txt":
        text = load_job_from_txt(str(path))
    elif suffix == ".docx":
        text = load_job_from_docx(str(path))
    elif suffix == ".pdf":
        text = load_job_from_pdf(str(path))
    else:
        raise ValueError(f"Unsupported job file type: {suffix}")

    return {
        "source_type": "file",
        "filename": path.name,
        "text": text
    }