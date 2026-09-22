import json
from pathlib import Path

from credit_rag.rag.chunk_cache import load_chunks
from credit_rag.rag.dense_retrieval import (
    EMBEDDINGS_PATH,
    load_embeddings,
    search_dense,
)
from credit_rag.rag.embeddings import load_embedding_model

GOLDEN_PATH = Path("evals/retrieval_golden.jsonl")


def load_golden_questions(
    path: str | Path = GOLDEN_PATH,
) -> list[dict]:
    path = Path(path)

    questions = []

    with path.open(
        "r",
        encoding="utf-8",
    ) as file:
        for line in file:
            line = line.strip()

            if not line:
                continue

            questions.append(json.loads(line))

    return questions


def recall_at_k(
    retrieved_pages: list[int],
    relevant_pages: list[int],
    k: int,
) -> float:
    retrieved_at_k = set(retrieved_pages[:k])
    relevant = set(relevant_pages)

    found = retrieved_at_k & relevant

    return len(found) / len(relevant)


def reciprocal_rank(
    retrieved_pages: list[int],
    relevant_pages: list[int],
) -> float:
    relevant = set(relevant_pages)

    for rank, page in enumerate(
        retrieved_pages,
        start=1,
    ):
        if page in relevant:
            return 1.0 / rank

    return 0.0

if __name__ == "__main__":
    golden_questions = load_golden_questions()

    chunks = load_chunks()

    print(f"Chunks loaded from cache: {len(chunks)}")

    chunk_embeddings = load_embeddings(
        EMBEDDINGS_PATH
    )

    if len(chunks) != len(chunk_embeddings):
        raise ValueError(
            "Chunks and embeddings count do not match"
        )

    model = load_embedding_model()

    recall_1_scores = []
    recall_3_scores = []
    recall_5_scores = []
    reciprocal_ranks = []

    for item in golden_questions:
        results = search_dense(
            query=item["question"],
            chunks=chunks,
            chunk_embeddings=chunk_embeddings,
            top_k=5,
            company=item["company"],
            year=item["year"],
            model=model,
        )

        retrieved_pages = [
            chunk.page
            for chunk, _ in results
        ]

        relevant_pages = item["relevant_pages"]

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

        print()
        print("=" * 100)
        print(f"{item['id']}: {item['question']}")
        print(f"GOLD: {relevant_pages}")
        print(f"TOP-5: {retrieved_pages}")
        print(
            f"R@1={r1:.2f} | "
            f"R@3={r3:.2f} | "
            f"R@5={r5:.2f} | "
            f"RR={rr:.2f}"
        )

    question_count = len(golden_questions)

    mean_recall_1 = (
        sum(recall_1_scores) / question_count
    )
    mean_recall_3 = (
        sum(recall_3_scores) / question_count
    )
    mean_recall_5 = (
        sum(recall_5_scores) / question_count
    )
    mrr = (
        sum(reciprocal_ranks) / question_count
    )

    print()
    print("#" * 100)
    print("BASELINE RETRIEVAL METRICS")
    print("#" * 100)
    print(f"Questions: {question_count}")
    print(f"Recall@1: {mean_recall_1:.3f}")
    print(f"Recall@3: {mean_recall_3:.3f}")
    print(f"Recall@5: {mean_recall_5:.3f}")
    print(f"MRR:      {mrr:.3f}")