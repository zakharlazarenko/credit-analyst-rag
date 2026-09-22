from typing import Any

from credit_rag.assistant.routing import (
    ParsedQuestion,
    QuestionIntent,
)
from credit_rag.rag.pipeline import RAGPipeline


class QualitativeRAGHandler:
    """
    Adapter между assistant dispatcher
    и существующим Text RAG pipeline.

    RAGPipeline создается один раз
    и переиспользуется между запросами.
    """

    def __init__(
        self,
        pipeline: RAGPipeline,
    ) -> None:
        self.pipeline = pipeline

    def __call__(
        self,
        question: str,
        parsed: ParsedQuestion,
    ) -> dict[str, Any]:
        """
        Выполняет qualitative-запрос
        через Text RAG branch.
        """

        if (
            parsed.intent
            != QuestionIntent.QUALITATIVE
        ):
            raise ValueError(
                "QualitativeRAGHandler получил "
                "не qualitative intent."
            )

        if len(parsed.company_ids) != 1:
            raise ValueError(
                "Для qualitative-запроса "
                "требуется одна компания."
            )

        if parsed.period is None:
            raise ValueError(
                "Для qualitative-запроса "
                "не указан период."
            )

        company_id = parsed.company_ids[0]

        try:
            year = int(
                parsed.period
            )

        except ValueError as error:
            raise ValueError(
                "Период qualitative-запроса "
                "должен быть годом."
            ) from error

        answer = self.pipeline.answer_question(
            question=question,
            company=company_id,
            year=year,
        )

        return {
            "tool": "retrieve_docs",
            "company_id": company_id,
            "period": str(year),
            "answer": answer,
        }