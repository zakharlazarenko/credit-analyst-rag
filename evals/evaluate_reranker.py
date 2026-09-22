import json
from pathlib import Path

from credit_rag.rag.chunk_cache import load_chunks
from credit_rag.rag.dense_retrieval import (
    EMBEDDINGS_PATH,
    load_embeddings,
    search_dense,
)
from credit_rag.rag.embeddings import load_embedding_model
from credit_rag.rag.reranker import (
    load_reranker,
    rerank,
)

GOLDEN_PATH = Path("evals/retrieval_golden.jsonl")


def load_golden(
    path: str | Path = GOLDEN_PATH,
) -> list[dict]:
    path = Path(path)

    items = []

    with path.open("r", encoding="utf-8") as file:
        for line in file:
            line = line.strip()

            if not line:
                continue

            items.append(json.loads(line))

    return items


def recall_at_k(
    retrieved_pages: list[int],
    relevant_pages: list[int],
    k: int,
) -> float:
    relevant_set = set(relevant_pages)

    if not relevant_set:
        return 0.0

    retrieved_at_k = set(
        retrieved_pages[:k]
    )

    found_relevant = (
        retrieved_at_k & relevant_set
    )

    return (
        len(found_relevant)
        / len(relevant_set)
    )


def reciprocal_rank(
    retrieved_pages: list[int],
    relevant_pages: list[int],
) -> float:
    relevant_set = set(relevant_pages)

    for rank, page in enumerate(
        retrieved_pages,
        start=1,
    ):
        if page in relevant_set:
            return 1.0 / rank

    return 0.0


if __name__ == "__main__":
    # ---------------------------------------------------------------
    # 1. Golden dataset
    # ---------------------------------------------------------------

    golden = load_golden()

    print(
        f"Golden questions loaded: "
        f"{len(golden)}"
    )

    # ---------------------------------------------------------------
    # 2. Offline artifacts
    # ---------------------------------------------------------------

    chunks = load_chunks()

    print(
        f"Chunks loaded from cache: "
        f"{len(chunks)}"
    )

    embeddings = load_embeddings(
        EMBEDDINGS_PATH
    )

    print(
        f"Embeddings: "
        f"{embeddings.shape}"
    )

    if len(chunks) != len(embeddings):
        raise ValueError(
            "Chunks and embeddings "
            "have different lengths."
        )

    # ---------------------------------------------------------------
    # 3. Models are loaded ONCE
    # ---------------------------------------------------------------

    print("Loading dense model...")

    dense_model = (
        load_embedding_model()
    )

    print("Loading reranker...")

    reranker_model = (
        load_reranker()
    )

    print("Models loaded")

    # ---------------------------------------------------------------
    # 4. Metrics
    # ---------------------------------------------------------------

    recall_1_scores = []
    recall_3_scores = []
    recall_5_scores = []
    reciprocal_ranks = []

    # ---------------------------------------------------------------
    # 5. Evaluation
    #
    # Corpus
    # → Dense Top-20
    # → Cross-Encoder
    # → Top-5
    # ---------------------------------------------------------------

    for item in golden:
        question = item["question"]
        company = item["company"]
        year = item["year"]
        relevant_pages = (
            item["relevant_pages"]
        )

        print()
        print(
            f"Processing {item['id']}..."
        )

        dense_results = search_dense(
            query=question,
            chunks=chunks,
            chunk_embeddings=embeddings,
            top_k=5,
            company=company,
            year=year,
            model=dense_model,
        )

        results = rerank(
            query=question,
            results=dense_results,
            model=reranker_model,
            top_k=5,
        )

        retrieved_pages = [
            chunk.page
            for chunk, score in results
        ]

        r1 = recall_at_k(
            retrieved_pages,
            relevant_pages,
            k=1,
        )

        r3 = recall_at_k(
            retrieved_pages,
            relevant_pages,
            k=3,
        )

        r5 = recall_at_k(
            retrieved_pages,
            relevant_pages,
            k=5,
        )

        rr = reciprocal_rank(
            retrieved_pages,
            relevant_pages,
        )

        recall_1_scores.append(r1)
        recall_3_scores.append(r3)
        recall_5_scores.append(r5)
        reciprocal_ranks.append(rr)

        print("=" * 100)
        print(
            f"{item['id']}: "
            f"{question}"
        )
        print(
            f"GOLD: "
            f"{relevant_pages}"
        )
        print(
            f"TOP-5: "
            f"{retrieved_pages}"
        )
        print(
            f"R@1={r1:.2f} | "
            f"R@3={r3:.2f} | "
            f"R@5={r5:.2f} | "
            f"RR={rr:.2f}"
        )

    # ---------------------------------------------------------------
    # 6. Aggregate metrics
    # ---------------------------------------------------------------

    if not golden:
        raise ValueError(
            "Golden dataset is empty"
        )

    mean_recall_1 = (
        sum(recall_1_scores)
        / len(recall_1_scores)
    )

    mean_recall_3 = (
        sum(recall_3_scores)
        / len(recall_3_scores)
    )

    mean_recall_5 = (
        sum(recall_5_scores)
        / len(recall_5_scores)
    )

    mean_mrr = (
        sum(reciprocal_ranks)
        / len(reciprocal_ranks)
    )

    print()
    print("#" * 100)
    print(
        "DENSE + RERANKER "
        "RETRIEVAL METRICS"
    )
    print("#" * 100)

    print(
        f"Questions: {len(golden)}"
    )
    print(
        f"Recall@1: "
        f"{mean_recall_1:.3f}"
    )
    print(
        f"Recall@3: "
        f"{mean_recall_3:.3f}"
    )
    print(
        f"Recall@5: "
        f"{mean_recall_5:.3f}"
    )
    print(
        f"MRR:      "
        f"{mean_mrr:.3f}"
    )
