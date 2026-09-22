from pathlib import Path

import pdfplumber

from credit_rag.rag.cleaning import normalize_text
from credit_rag.rag.manifest import load_manifest
from credit_rag.rag.schemas import PageDocument


def load_pdf_pages(
    pdf_path: str | Path,
    doc_id: str,
    company: str,
    year: int,
    doc_type: str,
) -> list[PageDocument]:
    pdf_path = Path(pdf_path)

    pages = []

    with pdfplumber.open(pdf_path) as pdf:
        for page_number, page in enumerate(pdf.pages, start=1):
            raw_text = page.extract_text() or ""

            clean_text = normalize_text(
                raw_text,
                page_number=page_number,
            )

            if not clean_text:
                continue

            page_document = PageDocument(
                doc_id=doc_id,
                company=company,
                year=year,
                doc_type=doc_type,
                page=page_number,
                text=clean_text,
            )

            pages.append(page_document)

    return pages

def load_corpus(
    raw_dir: str | Path = "data/raw",
) -> list[PageDocument]:
    raw_dir = Path(raw_dir)

    manifest_entries = load_manifest()

    documents = []

    for entry in manifest_entries:
        pdf_path = raw_dir / f"{entry.doc_id}.pdf"

        if not pdf_path.exists():
            raise FileNotFoundError(
                f"PDF not found: {pdf_path}"
            )

        pages = load_pdf_pages(
            pdf_path=pdf_path,
            doc_id=entry.doc_id,
            company=entry.company,
            year=entry.year,
            doc_type=entry.doc_type,
        )

        documents.extend(pages)

        print(
            f"{entry.doc_id}: "
            f"{len(pages)} pages loaded"
        )

    return documents

if __name__ == "__main__":
    documents = load_corpus()

    print()
    print(f"TOTAL PAGE DOCUMENTS: {len(documents)}")

    tatneft_pages = {
        document.page
        for document in documents
        if document.doc_id == "tatneft_ar_2024"
    }

    expected_pages = set(range(1, 201))
    missing_pages = sorted(expected_pages - tatneft_pages)

    print()
    print("MISSING TATNEFT 2024 PAGES:")
    print(missing_pages)