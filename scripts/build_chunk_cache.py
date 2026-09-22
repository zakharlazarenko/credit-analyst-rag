from credit_rag.rag.chunk_cache import (
    CHUNKS_PATH,
    save_chunks,
)
from credit_rag.rag.chunking import chunk_corpus
from credit_rag.rag.ingestion import load_corpus

if __name__ == "__main__":
    print("Loading PDFs...")

    documents = load_corpus()

    print()
    print(f"PageDocuments: {len(documents)}")

    print("Building chunks...")

    chunks = chunk_corpus(
        documents,
        chunk_size=1200,
        overlap=200,
    )

    print(f"Chunks: {len(chunks)}")

    print("Saving chunk cache...")

    save_chunks(
        chunks=chunks,
        path=CHUNKS_PATH,
    )

    print()
    print("DONE")
    print(f"Saved chunks: {len(chunks)}")
    print(f"Path: {CHUNKS_PATH}")