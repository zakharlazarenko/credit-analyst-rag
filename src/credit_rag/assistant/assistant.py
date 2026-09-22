from pathlib import Path

from credit_rag.assistant.answer_formatter import (
    format_dispatch_result,
)
from credit_rag.assistant.dispatcher import (
    DispatchResult,
    dispatch_question,
)
from credit_rag.assistant.qualitative import (
    QualitativeRAGHandler,
)
from credit_rag.assistant.question_parser import (
    parse_question,
)
from credit_rag.financial.fact_store import (
    load_facts,
)
from credit_rag.financial.schemas import FinancialFact
from credit_rag.rag.pipeline import RAGPipeline


class CreditAnalystAssistant:
    """
    Единая точка входа в помощника
    кредитного аналитика.

    Отвечает за orchestration:

    question
        ↓
    parser
        ↓
    dispatcher
        ↓
    RAG / financial tools
    """

    def __init__(
        self,
        fact_store_path: Path,
        rag_pipeline: RAGPipeline | None = None,
    ) -> None:
        """
        Загружает тяжелые компоненты один раз.

        Parameters
        ----------
        fact_store_path:
            Путь к structured FinancialFact Store.

        rag_pipeline:
            Можно передать уже созданный RAGPipeline.
            Если не передан, pipeline будет создан здесь.
        """

        self.fact_store_path = fact_store_path

        self.facts: list[FinancialFact] = (
            load_facts(
                fact_store_path
            )
        )

        if rag_pipeline is None:
            rag_pipeline = RAGPipeline()

        self.rag_pipeline = rag_pipeline

        self.qualitative_handler = (
            QualitativeRAGHandler(
                pipeline=self.rag_pipeline
            )
        )

    def ask(
        self,
        question: str,
    ) -> DispatchResult:
        """
        Выполняет полный путь обработки
        одного пользовательского вопроса.

        Natural language
            ↓
        ParsedQuestion
            ↓
        validation / resolution
            ↓
        dispatcher
            ↓
        tool result
        """

        if not question.strip():
            raise ValueError(
                "Вопрос не должен быть пустым."
            )

        parsed = parse_question(
            question
        )

        return dispatch_question(
            question=question,
            parsed=parsed,
            facts=self.facts,
            qualitative_handler=(
                self.qualitative_handler
            ),
        )

    def ask_text(
        self,
        question: str,
    ) -> str:
        """
        Выполняет полный pipeline
        и возвращает готовый
        пользовательский ответ.
        """

        result = self.ask(
            question
        )

        return format_dispatch_result(
            result
        )