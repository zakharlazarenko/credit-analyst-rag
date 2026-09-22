from pathlib import Path

import numpy as np

from credit_rag.rag.chunking import chunk_corpus
from credit_rag.rag.embeddings import load_embedding_model
from credit_rag.rag.ingestion import load_corpus
from credit_rag.rag.schemas import ChunkDocument

EMBEDDINGS_PATH = Path(
    "data/processed/chunk_embeddings.npy"
)


def build_chunk_embeddings(
    chunks: list[ChunkDocument],
) -> np.ndarray:
    model = load_embedding_model()

    passages = [
        f"passage: {chunk.text}"
        for chunk in chunks
    ]

    embeddings = model.encode(
        passages,
        batch_size=32,
        normalize_embeddings=True,
        show_progress_bar=True,
    )

    return embeddings


def search_dense(
    query: str,
    chunks: list[ChunkDocument],
    chunk_embeddings: np.ndarray,
    top_k: int = 5,
    company: str | None = None,
    year: int | None = None,
    model=None,
) -> list[tuple[ChunkDocument, float]]:
    if len(chunks) != len(chunk_embeddings):
        raise ValueError(
            "Number of chunks and embeddings must match"
        )

    candidate_indices = [
        index
        for index, chunk in enumerate(chunks)
        if (
            (company is None or chunk.company == company)
            and
            (year is None or chunk.year == year)
        )
    ]

    if not candidate_indices:
        return []

    candidate_embeddings = chunk_embeddings[
        candidate_indices
    ]

    if model is None:
        model = load_embedding_model()

    query_embedding = model.encode(
        f"query: {query}",
        normalize_embeddings=True,
    )

    scores = candidate_embeddings @ query_embedding

    top_local_indices = np.argsort(scores)[::-1][:top_k]

    results = [
        (
            chunks[candidate_indices[local_index]],
            float(scores[local_index]),
        )
        for local_index in top_local_indices
    ]

    return results

def save_embeddings(
    embeddings: np.ndarray,
    path: str | Path = EMBEDDINGS_PATH,
) -> None:
    path = Path(path)

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    np.save(path, embeddings)


def load_embeddings(
    path: str | Path = EMBEDDINGS_PATH,
) -> np.ndarray:
    path = Path(path)

    return np.load(path)

if __name__ == "__main__":
    documents = load_corpus()

    chunks = chunk_corpus(
        documents,
        chunk_size=1200,
        overlap=200,
    )

    print()
    print(f"CHUNKS: {len(chunks)}")

    if EMBEDDINGS_PATH.exists():
        print("Loading existing embeddings...")

        chunk_embeddings = load_embeddings()

    else:
        print("Building embeddings...")

        chunk_embeddings = build_chunk_embeddings(
            chunks
        )

        save_embeddings(
            chunk_embeddings
        )

        print(
            f"Saved embeddings to: "
            f"{EMBEDDINGS_PATH}"
        )

    print()
    print(
        "EMBEDDING MATRIX:",
        chunk_embeddings.shape,
    )

    query = (
        "Как ЛУКОЙЛ управлял "
        "климатическими рисками в 2024 году?"
    )

    results_without_filter = search_dense(
        query=query,
        chunks=chunks,
        chunk_embeddings=chunk_embeddings,
        top_k=5,
    )

    results_with_filter = search_dense(
        query=query,
        chunks=chunks,
        chunk_embeddings=chunk_embeddings,
        top_k=5,
        company="LUKOIL",
        year=2024,
    )

    filtered_chunks = [
        chunk
        for chunk in chunks
        if chunk.company == "LUKOIL"
           and chunk.year == 2024
    ]

    print()
    print("#" * 100)
    print("WITHOUT METADATA FILTER")
    print("#" * 100)

    for rank, (chunk, score) in enumerate(
            results_without_filter,
            start=1,
    ):
        print(
            f"{rank}. "
            f"{chunk.doc_id} | "
            f"page={chunk.page} | "
            f"score={score:.4f}"
        )

    print()
    print("#" * 100)
    print("WITH METADATA FILTER")
    print("#" * 100)

    for rank, (chunk, score) in enumerate(
            results_with_filter,
            start=1,
    ):
        print(
            f"{rank}. "
            f"{chunk.doc_id} | "
            f"page={chunk.page} | "
            f"score={score:.4f}"
        )