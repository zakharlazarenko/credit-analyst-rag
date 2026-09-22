import re

import numpy as np
from rank_bm25 import BM25Okapi

from credit_rag.rag.schemas import ChunkDocument


def tokenize_for_bm25(text: str) -> list[str]:
    """
    Простая токенизация для BM25.

    1. Приводим текст к нижнему регистру.
    2. Выделяем русские/английские слова, числа
       и конструкции с дефисами.
    """

    text = text.lower()

    return re.findall(
        r"[a-zа-яё0-9]+(?:[-–—][a-zа-яё0-9]+)*",
        text,
    )


class BM25Index:
    """
    Предварительно построенные BM25-индексы.

    Для каждой пары:
        (company, year)

    создаётся отдельный BM25 index.

    Например:
        ("LUKOIL", 2024)
        ("ROSNEFT", 2025)
        ("TATNEFT", 2024)

    Индекс строится один раз, после чего может использоваться
    для любого количества запросов.
    """

    def __init__(
        self,
        chunks: list[ChunkDocument],
    ) -> None:
        self.indexes: dict[
            tuple[str, int],
            tuple[list[ChunkDocument], BM25Okapi],
        ] = {}

        grouped_chunks: dict[
            tuple[str, int],
            list[ChunkDocument],
        ] = {}

        # ----------------------------------------------------------
        # 1. Разбиваем chunks по company + year
        # ----------------------------------------------------------

        for chunk in chunks:
            key = (
                chunk.company,
                chunk.year,
            )

            grouped_chunks.setdefault(
                key,
                [],
            ).append(chunk)

        # ----------------------------------------------------------
        # 2. Для каждой группы строим BM25 только ОДИН раз
        # ----------------------------------------------------------

        for key, group in grouped_chunks.items():
            tokenized_corpus = [
                tokenize_for_bm25(chunk.text)
                for chunk in group
            ]

            bm25 = BM25Okapi(
                tokenized_corpus
            )

            self.indexes[key] = (
                group,
                bm25,
            )

    def search(
        self,
        query: str,
        top_k: int,
        company: str,
        year: int,
    ) -> list[tuple[ChunkDocument, float]]:
        """
        Ищет top-k chunks внутри уже построенного
        company/year BM25-индекса.
        """

        key = (
            company,
            year,
        )

        if key not in self.indexes:
            return []

        candidate_chunks, bm25 = self.indexes[key]

        tokenized_query = tokenize_for_bm25(
            query
        )

        scores = bm25.get_scores(
            tokenized_query
        )

        top_indices = np.argsort(
            scores
        )[::-1][:top_k]

        return [
            (
                candidate_chunks[index],
                float(scores[index]),
            )
            for index in top_indices
        ]


def search_bm25(
    query: str,
    chunks: list[ChunkDocument],
    top_k: int = 5,
    company: str | None = None,
    year: int | None = None,
) -> list[tuple[ChunkDocument, float]]:
    """
    Старый простой интерфейс.

    Полезен для одиночных экспериментов, но при большом количестве
    запросов лучше использовать BM25Index, чтобы не перестраивать
    индекс каждый раз.
    """

    candidate_chunks = [
        chunk
        for chunk in chunks
        if (company is None or chunk.company == company)
        and (year is None or chunk.year == year)
    ]

    if not candidate_chunks:
        return []

    tokenized_corpus = [
        tokenize_for_bm25(chunk.text)
        for chunk in candidate_chunks
    ]

    bm25 = BM25Okapi(
        tokenized_corpus
    )

    tokenized_query = tokenize_for_bm25(
        query
    )

    scores = bm25.get_scores(
        tokenized_query
    )

    top_indices = np.argsort(
        scores
    )[::-1][:top_k]

    return [
        (
            candidate_chunks[index],
            float(scores[index]),
        )
        for index in top_indices
    ]