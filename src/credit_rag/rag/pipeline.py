from pathlib import Path

import numpy as np

from credit_rag.rag.chunk_cache import load_chunks
from credit_rag.rag.citations import format_answer_citations
from credit_rag.rag.context import build_context, build_context_sources
from credit_rag.rag.dense_retrieval import search_dense
from credit_rag.rag.embeddings import load_embedding_model
from credit_rag.rag.generation import generate_answer
from credit_rag.rag.prompting import build_system_prompt, build_user_prompt
from credit_rag.rag.reranker import load_reranker
from credit_rag.rag.schemas import ChunkDocument

PROJECT_DIR = Path(__file__).resolve().parents[3]

EMBEDDINGS_PATH = (
    PROJECT_DIR
    / "data"
    / "processed"
    / "chunk_embeddings.npy"
)

TOP_K = 5


class RAGPipeline:
    """
    Объединяет retrieval, reranking, построение контекста
    и генерацию ответа в единый RAG pipeline.
    """

    def __init__(self) -> None:
        self.chunks = load_chunks()
        self.embeddings = np.load(EMBEDDINGS_PATH)

        self.dense_model = load_embedding_model()
        self.reranker_model = load_reranker()

    @staticmethod
    def _extract_chunk(result: object) -> ChunkDocument:
        """
        Извлекает ChunkDocument из результата Dense-поиска.
        """
        if isinstance(result, ChunkDocument):
            return result

        if (
            isinstance(result, tuple)
            and len(result) >= 1
            and isinstance(result[0], ChunkDocument)
        ):
            return result[0]

        raise TypeError(
            f"Неизвестный формат результата поиска: {type(result)}"
        )

    def _rerank_chunks(
        self,
        question: str,
        chunks: list[ChunkDocument],
    ) -> list[ChunkDocument]:
        """
        Меняет порядок Dense Top-K без изменения состава чанков.
        """
        pairs = [
            (question, chunk.text)
            for chunk in chunks
        ]

        scores = self.reranker_model.predict(pairs)

        scored_chunks = [
            (chunk, float(score))
            for chunk, score in zip(chunks, scores, strict=True)
        ]

        scored_chunks.sort(
            key=lambda item: item[1],
            reverse=True,
        )

        return [
            chunk
            for chunk, _ in scored_chunks
        ]

    def retrieve(
        self,
        question: str,
        company: str,
        year: int,
    ) -> list[ChunkDocument]:
        """
        Выполняет Dense retrieval и reranking для заданного вопроса.
        """
        dense_results = search_dense(
            query=question,
            chunks=self.chunks,
            chunk_embeddings=self.embeddings,
            top_k=TOP_K,
            company=company,
            year=year,
            model=self.dense_model,
        )

        dense_chunks = [
            self._extract_chunk(result)
            for result in dense_results
        ]

        return self._rerank_chunks(
            question=question,
            chunks=dense_chunks,
        )

    def answer_question(
        self,
        question: str,
        company: str,
        year: int,
    ) -> str:
        """
        Выполняет полный RAG pipeline и возвращает grounded-ответ.
        """
        retrieved_chunks = self.retrieve(
            question=question,
            company=company,
            year=year,
        )

        sources = build_context_sources(
            retrieved_chunks
        )

        context = build_context(
            retrieved_chunks
        )

        system_prompt = build_system_prompt()

        user_prompt = build_user_prompt(
            question=question,
            context=context,
        )

        raw_answer = generate_answer(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
        )

        return format_answer_citations(
            answer=raw_answer,
            sources=sources,
        )