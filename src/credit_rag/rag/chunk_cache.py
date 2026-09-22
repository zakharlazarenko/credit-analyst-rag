from pathlib import Path

from credit_rag.rag.schemas import ChunkDocument

CHUNKS_PATH = Path(
    "data/processed/chunks_size1200_overlap200.jsonl"
)


def save_chunks(
    chunks: list[ChunkDocument],
    path: str | Path = CHUNKS_PATH,
) -> None:
    """
    Сохраняет готовые ChunkDocument в JSONL.

    Один chunk = одна строка JSON.
    """

    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("w", encoding="utf-8") as file:
        for chunk in chunks:
            file.write(chunk.model_dump_json())
            file.write("\n")


def load_chunks(
    path: str | Path = CHUNKS_PATH,
) -> list[ChunkDocument]:
    """
    Загружает готовые ChunkDocument из JSONL.
    """

    path = Path(path)

    if not path.exists():
        raise FileNotFoundError(
            f"Chunk cache not found: {path}"
        )

    chunks = []

    with path.open("r", encoding="utf-8") as file:
        for line in file:
            line = line.strip()

            if not line:
                continue

            chunk = ChunkDocument.model_validate_json(line)
            chunks.append(chunk)

    return chunks