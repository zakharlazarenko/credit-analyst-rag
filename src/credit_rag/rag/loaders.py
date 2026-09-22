from pathlib import Path

import pdfplumber
import pymupdf
from pypdf import PdfReader


def extract_page_text_pypdf(
    pdf_path: str | Path,
    page_number: int,
) -> str:
    pdf_path = Path(pdf_path)

    reader = PdfReader(pdf_path)
    page = reader.pages[page_number - 1]

    text = page.extract_text()

    return text or ""

def extract_page_text_pdfplumber(
    pdf_path: str | Path,
    page_number: int,
) -> str:
    pdf_path = Path(pdf_path)

    with pdfplumber.open(pdf_path) as pdf:
        page = pdf.pages[page_number - 1]
        text = page.extract_text()

    return text or ""

def extract_page_table_pdfplumber(
    pdf_path: str | Path,
    page_number: int,
) -> list[list[str | None]] | None:
    pdf_path = Path(pdf_path)

    with pdfplumber.open(pdf_path) as pdf:
        page = pdf.pages[page_number - 1]
        table = page.extract_table()

    return table

def extract_page_text_pymupdf(
    pdf_path: str | Path,
    page_number: int,
) -> str:
    pdf_path = Path(pdf_path)

    with pymupdf.open(pdf_path) as pdf:
        page = pdf[page_number - 1]
        text = page.get_text("text")

    return text or ""

def inspect_page_words(
    pdf_path: str | Path,
    page_number: int,
) -> list[dict]:
    pdf_path = Path(pdf_path)

    with pdfplumber.open(pdf_path) as pdf:
        page = pdf.pages[page_number - 1]

        words = page.extract_words(
            extra_attrs=["fontname", "size"],
        )

    return words

def extract_styled_lines(
    pdf_path: str | Path,
    page_number: int,
) -> list[dict]:
    pdf_path = Path(pdf_path)

    with pdfplumber.open(pdf_path) as pdf:
        page = pdf.pages[page_number - 1]

        words = page.extract_words(
            extra_attrs=["fontname", "size"],
        )

    lines = {}

    for word in words:
        line_key = round(word["top"], 1)

        if line_key not in lines:
            lines[line_key] = []

        lines[line_key].append(word)

    result = []

    for line_key in sorted(lines):
        line_words = sorted(
            lines[line_key],
            key=lambda word: word["x0"],
        )

        text = " ".join(
            word["text"]
            for word in line_words
        )

        bold_words = [
            word
            for word in line_words
            if "Bold" in word["fontname"]
        ]

        bold_ratio = (
            len(bold_words) / len(line_words)
            if line_words
            else 0
        )

        result.append(
            {
                "text": text,
                "bold_ratio": bold_ratio,
            }
        )

    return result