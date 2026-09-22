import json
from pathlib import Path

from credit_rag.rag.bm25_retrieval import BM25Index
from credit_rag.rag.chunk_cache import load_chunks
from credit_rag.rag.dense_retrieval import (
    EMBEDDINGS_PATH,
    load_embeddings,
)
from credit_rag.rag.embeddings import load_embedding_model
from credit_rag.rag.hybrid_retrieval import search_hybrid

GOLDEN_PATH = Path("evals/retrieval_golden.jsonl")


def load_golden(
    path: str | Path = GOLDEN_PATH,
) -> list[dict]:
    """
    Загружает golden dataset из JSONL.
    """

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
    """
    Показывает, какую долю всех релевантных страниц
    мы нашли среди первых k результатов.
    """

    relevant_set = set(relevant_pages)

    if not relevant_set:
        return 0.0

    retrieved_at_k = set(retrieved_pages[:k])

    found_relevant = retrieved_at_k & relevant_set

    return len(found_relevant) / len(relevant_set)


def reciprocal_rank(
    retrieved_pages: list[int],
    relevant_pages: list[int],
) -> float:
    """
    Reciprocal Rank = 1 / rank первого релевантного результата.
    """

    relevant_set = set(relevant_pages)

    for rank, page in enumerate(retrieved_pages, start=1):
        if page in relevant_set:
            return 1.0 / rank

    return 0.0


if __name__ == "__main__":
    # ---------------------------------------------------------------
    # 1. Golden dataset
    # ---------------------------------------------------------------

    golden = load_golden()

    print(f"Golden questions loaded: {len(golden)}")

    # ---------------------------------------------------------------
    # 2. Corpus
    # ---------------------------------------------------------------

    chunks = load_chunks()

    print(f"Chunks loaded from cache: {len(chunks)}")

    print("Building BM25 indexes...")

    bm25_index = BM25Index(chunks)

    print(f"BM25 indexes: {len(bm25_index.indexes)}")

    # ---------------------------------------------------------------
    # 3. Загружаем заранее рассчитанные Dense embeddings
    #
    # Они нужны Hybrid, потому что один из двух retriever —
    # Dense retrieval.
    # ---------------------------------------------------------------

    embeddings = load_embeddings(EMBEDDINGS_PATH)

    if len(chunks) != len(embeddings):
        raise ValueError(
            "Chunks and embeddings have different lengths. "
            "Rebuild embeddings before evaluation."
        )

    print(f"Embeddings: {embeddings.shape}")

    # ---------------------------------------------------------------
    # 4. Загружаем embedding model один раз.
    #
    # Она нужна для превращения каждого query в embedding.
    # ---------------------------------------------------------------

    model = load_embedding_model()

    # ---------------------------------------------------------------
    # 5. Контейнеры для итоговых метрик
    # ---------------------------------------------------------------

    recall_1_scores = []
    recall_3_scores = []
    recall_5_scores = []
    reciprocal_ranks = []

    # ---------------------------------------------------------------
    # 6. Каждый golden question прогоняем через Hybrid
    # ---------------------------------------------------------------

    for item in golden:
        question = item["question"]
        company = item["company"]
        year = item["year"]
        relevant_pages = item["relevant_pages"]

        results = search_hybrid(
            query=question,
            chunks=chunks,
            chunk_embeddings=embeddings,
            top_k=5,
            candidate_k=20,
            company=company,
            year=year,
            model=model,
            rrf_k=60,
            bm25_index=bm25_index,
            dense_weight=2.0,
            bm25_weight=1.0,
        )

        retrieved_pages = [
            chunk.page
            for chunk, score in results
        ]

        # -----------------------------------------------------------
        # 7. Метрики текущего вопроса
        # -----------------------------------------------------------

        r1 = recall_at_k(
            retrieved_pages=retrieved_pages,
            relevant_pages=relevant_pages,
            k=1,
        )

        r3 = recall_at_k(
            retrieved_pages=retrieved_pages,
            relevant_pages=relevant_pages,
            k=3,
        )

        r5 = recall_at_k(
            retrieved_pages=retrieved_pages,
            relevant_pages=relevant_pages,
            k=5,
        )

        rr = reciprocal_rank(
            retrieved_pages=retrieved_pages,
            relevant_pages=relevant_pages,
        )

        recall_1_scores.append(r1)
        recall_3_scores.append(r3)
        recall_5_scores.append(r5)
        reciprocal_ranks.append(rr)

        # -----------------------------------------------------------
        # 8. Результат отдельного вопроса
        # -----------------------------------------------------------

        print()
        print("=" * 100)
        print(f"{item['id']}: {question}")
        print(f"GOLD: {relevant_pages}")
        print(f"TOP-5: {retrieved_pages}")
        print(
            f"R@1={r1:.2f} | "
            f"R@3={r3:.2f} | "
            f"R@5={r5:.2f} | "
            f"RR={rr:.2f}"
        )

    # ---------------------------------------------------------------
    # 9. Средние метрики
    # ---------------------------------------------------------------

    if not golden:
        raise ValueError("Golden dataset is empty")

    mean_recall_1 = sum(recall_1_scores) / len(recall_1_scores)
    mean_recall_3 = sum(recall_3_scores) / len(recall_3_scores)
    mean_recall_5 = sum(recall_5_scores) / len(recall_5_scores)
    mean_mrr = sum(reciprocal_ranks) / len(reciprocal_ranks)

    # ---------------------------------------------------------------
    # 10. Hybrid Baseline
    # ---------------------------------------------------------------

    print()
    print("#" * 100)
    print("HYBRID BASELINE RETRIEVAL METRICS")
    print("#" * 100)

    print(f"Questions: {len(golden)}")
    print(f"Recall@1: {mean_recall_1:.3f}")
    print(f"Recall@3: {mean_recall_3:.3f}")
    print(f"Recall@5: {mean_recall_5:.3f}")
    print(f"MRR:      {mean_mrr:.3f}")