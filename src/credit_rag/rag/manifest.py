import csv
from pathlib import Path

from credit_rag.rag.schemas import ManifestEntry

MANIFEST_PATH = Path("data/raw/MANIFEST.csv")


def load_manifest(
    manifest_path: str | Path = MANIFEST_PATH,
) -> list[ManifestEntry]:
    manifest_path = Path(manifest_path)

    entries = []

    with manifest_path.open(
        "r",
        encoding="utf-8-sig",
        newline="",
    ) as file:
        reader = csv.DictReader(file)

        for row in reader:
            entry = ManifestEntry(
                doc_id=row["doc_id"],
                company=row["company"],
                year=row["year"],
                doc_type=row["type"],
                url=row["url"],
                sha256=row["sha256"],
                pages=row["pages"],
            )

            entries.append(entry)

    return entries


if __name__ == "__main__":
    entries = load_manifest()

    print(f"DOCUMENTS: {len(entries)}")

    for entry in entries:
        print(
            entry.doc_id,
            entry.company,
            entry.year,
            entry.pages,
        )