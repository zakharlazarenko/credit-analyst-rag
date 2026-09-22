from hashlib import sha256
from pathlib import Path

from pypdf import PdfReader


def calculate_sha256(file_path: str | Path) -> str:
    file_path = Path(file_path)

    hasher = sha256()

    with file_path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            hasher.update(chunk)

    return hasher.hexdigest()


def get_pdf_page_count(file_path: str | Path) -> int:
    file_path = Path(file_path)

    reader = PdfReader(file_path)

    return len(reader.pages)


if __name__ == "__main__":
    raw_dir = Path("data/raw")

    pdf_files = sorted(raw_dir.glob("*.pdf"))

    for pdf_path in pdf_files:
        print(f"File: {pdf_path.name}")
        print(f"SHA256: {calculate_sha256(pdf_path)}")
        print(f"Pages: {get_pdf_page_count(pdf_path)}")
        print("-" * 80)