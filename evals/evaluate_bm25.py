import json
from pathlib import Path

from credit_rag.rag.bm25_retrieval import BM25Index
from credit_rag.rag.chunk_cache import load_chunks

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

    retrieved_at_k = set(retrieved_pages[:k])

    found_relevant = retrieved_at_k & relevant_set

    return len(found_relevant) / len(relevant_set)


def reciprocal_rank(
    retrieved_pages: list[int],
    relevant_pages: list[int],
) -> float:

    relevant_set = set(relevant_pages)

    for rank, page in enumerate(retrieved_pages, start=1):
        if page in relevant_set:
            return 1.0 / rank

    return 0.0


if __name__ == "__main__":

    golden = load_golden()

    print(f"Golden questions loaded: {len(golden)}")

    chunks = load_chunks()

    print(f"Chunks loaded from cache: {len(chunks)}")

    print("Building BM25 indexes...")

    bm25_index = BM25Index(chunks)

    print(f"BM25 indexes: {len(bm25_index.indexes)}")

    print(f"Chunks: {len(chunks)}")

    recall_1_scores = []
    recall_3_scores = []
    recall_5_scores = []
    reciprocal_ranks = []

    for item in golden:
        question = item["question"]
        company = item["company"]
        year = item["year"]
        relevant_pages = item["relevant_pages"]

        results = bm25_index.search(
            query=question,
            top_k=5,
            company=company,
            year=year,
        )

        retrieved_pages = [
            chunk.page
            for chunk, score in results
        ]

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

    if not golden:
        raise ValueError("Golden dataset is empty")

    mean_recall_1 = sum(recall_1_scores) / len(recall_1_scores)
    mean_recall_3 = sum(recall_3_scores) / len(recall_3_scores)
    mean_recall_5 = sum(recall_5_scores) / len(recall_5_scores)
    mean_mrr = sum(reciprocal_ranks) / len(reciprocal_ranks)

    print()
    print("#" * 100)
    print("BM25 BASELINE RETRIEVAL METRICS")
    print("#" * 100)

    print(f"Questions: {len(golden)}")
    print(f"Recall@1: {mean_recall_1:.3f}")
    print(f"Recall@3: {mean_recall_3:.3f}")
    print(f"Recall@5: {mean_recall_5:.3f}")
    print(f"MRR:      {mean_mrr:.3f}")