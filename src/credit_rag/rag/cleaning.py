import re
from pathlib import Path

from credit_rag.rag.loaders import extract_page_text_pdfplumber


def normalize_text(
    text: str,
    page_number: int | None = None,
) -> str:
    text = text.replace("\u00a0", " ")

    lines = []

    for line in text.splitlines():
        line = re.sub(r"[ \t]+", " ", line)
        line = line.strip()

        if page_number is not None and line == str(page_number):
            continue

        lines.append(line)

    normalized_text = "\n".join(lines)

    normalized_text = re.sub(
        r"\n{3,}",
        "\n\n",
        normalized_text,
    )

    return normalized_text.strip()


if __name__ == "__main__":
    pdf_path = Path("data/raw/lukoil_ar_2024.pdf")

    raw_text = extract_page_text_pdfplumber(
        pdf_path,
        page_number=28,
    )

    clean_text = normalize_text(
        raw_text,
        page_number=28,
    )

    print("=" * 100)
    print("RAW")
    print("=" * 100)
    print(raw_text)

    print()

    print("=" * 100)
    print("NORMALIZED")
    print("=" * 100)
    print(clean_text)