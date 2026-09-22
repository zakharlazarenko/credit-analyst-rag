from credit_rag.rag.bm25_retrieval import BM25Index, search_bm25
from credit_rag.rag.dense_retrieval import search_dense
from credit_rag.rag.schemas import ChunkDocument


def reciprocal_rank_fusion(
    dense_results: list[tuple[ChunkDocument, float]],
    bm25_results: list[tuple[ChunkDocument, float]],
    top_k: int = 5,
    rrf_k: int = 60,
    dense_weight: float = 2.0,
    bm25_weight: float = 1.0,
) -> list[tuple[ChunkDocument, float]]:
    """
    Weighted Reciprocal Rank Fusion.

    Dense получает больший вес, потому что на нашем baseline
    он показывает существенно более высокое качество, чем BM25.
    """

    rrf_scores: dict[str, float] = {}
    chunks_by_id: dict[str, ChunkDocument] = {}

    # Dense ranking
    for rank, (chunk, _) in enumerate(
        dense_results,
        start=1,
    ):
        chunk_id = chunk.chunk_id

        chunks_by_id[chunk_id] = chunk

        rrf_scores[chunk_id] = (
            rrf_scores.get(chunk_id, 0.0)
            + dense_weight / (rrf_k + rank)
        )

    # BM25 ranking
    for rank, (chunk, _) in enumerate(
        bm25_results,
        start=1,
    ):
        chunk_id = chunk.chunk_id

        chunks_by_id[chunk_id] = chunk

        rrf_scores[chunk_id] = (
            rrf_scores.get(chunk_id, 0.0)
            + bm25_weight / (rrf_k + rank)
        )

    sorted_chunk_ids = sorted(
        rrf_scores,
        key=rrf_scores.get,
        reverse=True,
    )

    return [
        (
            chunks_by_id[chunk_id],
            rrf_scores[chunk_id],
        )
        for chunk_id in sorted_chunk_ids[:top_k]
    ]


def search_hybrid(
    query: str,
    chunks: list[ChunkDocument],
    chunk_embeddings,
    top_k: int = 5,
    candidate_k: int = 20,
    company: str | None = None,
    year: int | None = None,
    model=None,
    rrf_k: int = 60,
    bm25_index: BM25Index | None = None,
    dense_weight: float = 2.0,
    bm25_weight: float = 1.0,
) -> list[tuple[ChunkDocument, float]]:

    dense_results = search_dense(
        query=query,
        chunks=chunks,
        chunk_embeddings=chunk_embeddings,
        top_k=candidate_k,
        company=company,
        year=year,
        model=model,
    )

    if bm25_index is not None:
        if company is None or year is None:
            raise ValueError(
                "company and year are required when using BM25Index"
            )

        bm25_results = bm25_index.search(
            query=query,
            top_k=candidate_k,
            company=company,
            year=year,
        )
    else:
        bm25_results = search_bm25(
            query=query,
            chunks=chunks,
            top_k=candidate_k,
            company=company,
            year=year,
        )

    return reciprocal_rank_fusion(
        dense_results=dense_results,
        bm25_results=bm25_results,
        top_k=top_k,
        rrf_k=rrf_k,
        dense_weight=dense_weight,
        bm25_weight=bm25_weight,
    )