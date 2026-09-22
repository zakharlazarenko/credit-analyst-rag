from __future__ import annotations

from collections.abc import Sequence

import torch
from transformers import (
    AutoModelForSequenceClassification,
    AutoTokenizer,
)

RERANKER_MODEL_NAME = (
    "Alibaba-NLP/gte-multilingual-reranker-base"
)



class GTEReranker:
    """
    GTE multilingual reranker.

    Используем Transformers напрямую,
    а не sentence_transformers.CrossEncoder.

    Модель и tokenizer загружаются
    только из локального Hugging Face cache.
    """

    def __init__(
        self,
        model_name: str = RERANKER_MODEL_NAME,
        device: str | None = None,
        max_length: int = 512,
        batch_size: int = 8,
    ) -> None:
        """
        Инициализирует reranker.

        Parameters
        ----------
        model_name:
            Идентификатор модели Hugging Face.

        device:
            cpu / cuda.
            Если None, устройство выбирается автоматически.

        max_length:
            Максимальная длина пары
            query + passage в токенах.

        batch_size:
            Размер batch при inference.
        """

        self.model_name = model_name
        self.max_length = max_length
        self.batch_size = batch_size

        if device is None:
            device = (
                "cuda"
                if torch.cuda.is_available()
                else "cpu"
            )

        self.device = torch.device(
            device
        )

        print(
            f"Reranker device: {self.device}"
        )

        # -------------------------------------------------
        # Tokenizer
        # -------------------------------------------------
        #
        # local_files_only=True запрещает обращения
        # к huggingface.co.
        # Используется уже скачанный локальный cache.
        # -------------------------------------------------

        self.tokenizer = (
            AutoTokenizer.from_pretrained(
                model_name,
                trust_remote_code=True,
                local_files_only=True,
            )
        )

        # -------------------------------------------------
        # Model
        # -------------------------------------------------

        self.model = (
            AutoModelForSequenceClassification
            .from_pretrained(
                model_name,
                trust_remote_code=True,
                local_files_only=True,
            )
        )

        self.model.to(
            self.device
        )

        self.model.eval()

    def predict(
        self,
        pairs: Sequence[
            tuple[str, str]
        ],
        batch_size: int | None = None,
    ) -> list[float]:
        """
        Рассчитывает relevance score
        для пар:

        (query, passage)

        Метод сохранён для совместимости
        с предыдущим интерфейсом reranker.
        """

        if not pairs:
            return []

        effective_batch_size = (
            batch_size
            if batch_size is not None
            else self.batch_size
        )

        scores: list[float] = []

        for start in range(
            0,
            len(pairs),
            effective_batch_size,
        ):
            batch = pairs[
                start:
                start + effective_batch_size
            ]

            queries = [
                query
                for query, _ in batch
            ]

            passages = [
                passage
                for _, passage in batch
            ]

            encoded = self.tokenizer(
                queries,
                passages,
                padding=True,
                truncation=True,
                max_length=self.max_length,
                return_tensors="pt",
            )

            encoded = {
                key: value.to(
                    self.device
                )
                for key, value
                in encoded.items()
            }

            with torch.inference_mode():
                outputs = self.model(
                    **encoded
                )

            batch_scores = (
                outputs.logits
                .view(-1)
                .float()
                .cpu()
                .tolist()
            )

            scores.extend(
                batch_scores
            )

        return scores

    def score_pairs(
        self,
        query: str,
        passages: Sequence[str],
    ) -> list[float]:
        """
        Удобная обёртка для scoring:

        query
        +
        список passages.
        """

        pairs = [
            (
                query,
                passage,
            )
            for passage in passages
        ]

        return self.predict(
            pairs=pairs,
        )

    @staticmethod
    def _extract_text(
        candidate: object,
    ) -> str:
        """
        Извлекает текст из retrieval candidate.

        Поддерживает:
        - str;
        - объект с .text;
        - объект с .chunk.text;
        - dict["text"];
        - dict["chunk"]["text"].
        """

        if isinstance(
            candidate,
            str,
        ):
            return candidate

        if isinstance(
            candidate,
            dict,
        ):
            if "text" in candidate:
                return str(
                    candidate["text"]
                )

            chunk = candidate.get(
                "chunk"
            )

            if (
                chunk is not None
                and isinstance(
                    chunk,
                    dict,
                )
                and "text" in chunk
            ):
                return str(
                    chunk["text"]
                )

            if (
                chunk is not None
                and hasattr(
                    chunk,
                    "text",
                )
            ):
                return str(
                    chunk.text
                )

        if hasattr(
            candidate,
            "text",
        ):
            return str(
                candidate.text
            )

        if hasattr(
            candidate,
            "chunk",
        ):
            chunk = candidate.chunk

            if hasattr(
                chunk,
                "text",
            ):
                return str(
                    chunk.text
                )

        raise TypeError(
            "Не удалось извлечь текст "
            "из кандидата для reranker. "
            f"Тип: {type(candidate)!r}"
        )

    def rerank[T](
        self,
        query: str,
        candidates: Sequence[T],
        top_k: int | None = None,
    ) -> list[T]:
        """
        Переранжирует retrieval candidates
        по relevance score.

        Возвращает исходные объекты,
        но в новом порядке.
        """

        if not candidates:
            return []

        passages = [
            self._extract_text(
                candidate
            )
            for candidate in candidates
        ]

        scores = self.score_pairs(
            query=query,
            passages=passages,
        )

        ranked = sorted(
            zip(
                candidates,
                scores,
                strict=True,
            ),
            key=lambda item: item[1],
            reverse=True,
        )

        if top_k is not None:
            ranked = ranked[
                :top_k
            ]

        return [
            candidate
            for candidate, _ in ranked
        ]


def load_reranker(
    model_name: str = RERANKER_MODEL_NAME,
    device: str | None = None,
) -> GTEReranker:
    """
    Загружает reranker.

    Эта функция является публичным интерфейсом,
    который использует RAGPipeline.
    """

    return GTEReranker(
        model_name=model_name,
        device=device,
    )


def rerank[T](
    query: str,
    results: Sequence[T],
    model: GTEReranker,
    top_k: int = 5,
) -> list[T]:
    """
    Совместимый module-level интерфейс
    для reranking retrieval results.

    Сохранён, чтобы не ломать существующий
    RAG pipeline и тесты.
    """

    return model.rerank(
        query=query,
        candidates=results,
        top_k=top_k,
    )