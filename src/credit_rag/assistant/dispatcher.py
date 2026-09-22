from collections.abc import Callable, Sequence
from dataclasses import dataclass
from enum import StrEnum
from typing import Any

from credit_rag.assistant.resolution import (
    resolve_growth_periods,
)
from credit_rag.assistant.routing import (
    ParsedQuestion,
    QuestionIntent,
)
from credit_rag.assistant.validation import (
    ParsedQuestionStatus,
    validate_parsed_question,
)
from credit_rag.financial.schemas import FinancialFact
from credit_rag.financial.tools import (
    calculate_financial_growth,
    compare_financial_companies,
    compute_financial_metric,
    query_financial_facts,
)


class DispatchStatus(StrEnum):
    """
    Результат выполнения dispatcher.
    """

    COMPLETED = "completed"

    NEEDS_CLARIFICATION = "needs_clarification"

    UNSUPPORTED = "unsupported"

    ERROR = "error"


@dataclass(frozen=True)
class DispatchResult:
    """
    Результат маршрутизации и выполнения
    пользовательского запроса.
    """

    status: DispatchStatus

    tool_name: str | None

    parsed_question: ParsedQuestion

    payload: dict[str, Any] | None

    message: str


# Dispatcher не должен зависеть
# от конкретной реализации RAGPipeline.
#
# Позже мы передадим сюда настоящий
# qualitative handler.
QualitativeHandler = Callable[
    [str, ParsedQuestion],
    dict[str, Any],
]


def dispatch_question(
    question: str,
    parsed: ParsedQuestion,
    facts: Sequence[FinancialFact],
    qualitative_handler: QualitativeHandler | None = None,
) -> DispatchResult:
    """
    Проверяет ParsedQuestion, при необходимости
    разрешает недостающие аргументы и вызывает
    соответствующий инструмент.
    """

    current_question = parsed

    # -------------------------------------------------
    # 1. Первая валидация
    # -------------------------------------------------

    validation = validate_parsed_question(
        current_question
    )

    if (
        validation.status
        == ParsedQuestionStatus.INVALID
    ):
        return DispatchResult(
            status=DispatchStatus.ERROR,
            tool_name=None,
            parsed_question=current_question,
            payload=None,
            message=(
                "Некорректный структурированный запрос: "
                + "; ".join(validation.errors)
            ),
        )

    # -------------------------------------------------
    # 2. Resolver для неполного growth
    # -------------------------------------------------

    if (
        validation.status
        == ParsedQuestionStatus.INCOMPLETE
        and current_question.intent
        == QuestionIntent.GROWTH
    ):
        resolution = resolve_growth_periods(
            parsed=current_question,
            facts=facts,
        )

        current_question = (
            resolution.parsed_question
        )

        validation = validate_parsed_question(
            current_question
        )

    # -------------------------------------------------
    # 3. Если обязательных данных всё ещё не хватает
    # -------------------------------------------------

    if (
        validation.status
        == ParsedQuestionStatus.INCOMPLETE
    ):
        return DispatchResult(
            status=(
                DispatchStatus.NEEDS_CLARIFICATION
            ),
            tool_name=None,
            parsed_question=current_question,
            payload=None,
            message=(
                "Для выполнения запроса "
                "не хватает параметров: "
                + ", ".join(
                    validation.missing_fields
                )
            ),
        )

    # -------------------------------------------------
    # 4. UNKNOWN
    # -------------------------------------------------

    if (
        current_question.intent
        == QuestionIntent.UNKNOWN
    ):
        return DispatchResult(
            status=DispatchStatus.UNSUPPORTED,
            tool_name=None,
            parsed_question=current_question,
            payload=None,
            message=(
                "Для этого запроса пока нет "
                "подходящего инструмента."
            ),
        )

    # -------------------------------------------------
    # 5. QUALITATIVE → RAG handler
    # -------------------------------------------------

    if (
        current_question.intent
        == QuestionIntent.QUALITATIVE
    ):
        if qualitative_handler is None:
            return DispatchResult(
                status=DispatchStatus.ERROR,
                tool_name="retrieve_docs",
                parsed_question=current_question,
                payload=None,
                message=(
                    "Qualitative handler "
                    "не настроен."
                ),
            )

        try:
            payload = qualitative_handler(
                question,
                current_question,
            )


        # Boundary внешнего qualitative handler:
        # превращаем неожиданный сбой RAG в контролируемый DispatchResult.
        except Exception as error:  # noqa: BLE001
            return DispatchResult(
                status=DispatchStatus.ERROR,
                tool_name="retrieve_docs",
                parsed_question=current_question,
                payload=None,
                message=str(error),
            )

        return DispatchResult(
            status=DispatchStatus.COMPLETED,
            tool_name="retrieve_docs",
            parsed_question=current_question,
            payload=payload,
            message=(
                "Qualitative-запрос выполнен."
            ),
        )

    # После VALID эти значения должны
    # существовать для numeric intents.
    metric = current_question.metric

    if metric is None:
        return DispatchResult(
            status=DispatchStatus.ERROR,
            tool_name=None,
            parsed_question=current_question,
            payload=None,
            message=(
                "После валидации отсутствует metric."
            ),
        )

    try:
        # -------------------------------------------------
        # 6. FACT
        # -------------------------------------------------

        if (
            current_question.intent
            == QuestionIntent.FACT
        ):
            company_id = (
                current_question.company_ids[0]
            )

            period = current_question.period

            if period is None:
                raise ValueError(
                    "Для fact отсутствует period."
                )

            payload = query_financial_facts(
                facts=facts,
                company_id=company_id,
                period=period,
                metric=metric,
            )

            return DispatchResult(
                status=DispatchStatus.COMPLETED,
                tool_name="query_facts",
                parsed_question=current_question,
                payload=payload,
                message=(
                    "Финансовый факт найден."
                ),
            )

        # -------------------------------------------------
        # 7. DERIVED METRIC
        # -------------------------------------------------

        if (
            current_question.intent
            == QuestionIntent.DERIVED_METRIC
        ):
            company_id = (
                current_question.company_ids[0]
            )

            period = current_question.period

            if period is None:
                raise ValueError(
                    "Для derived_metric "
                    "отсутствует period."
                )

            payload = compute_financial_metric(
                facts=facts,
                company_id=company_id,
                period=period,
                metric=metric,
            )

            return DispatchResult(
                status=DispatchStatus.COMPLETED,
                tool_name="compute_metric",
                parsed_question=current_question,
                payload=payload,
                message=(
                    "Расчетная метрика вычислена."
                ),
            )

        # -------------------------------------------------
        # 8. COMPARISON
        # -------------------------------------------------

        if (
            current_question.intent
            == QuestionIntent.COMPARISON
        ):
            period = current_question.period

            if period is None:
                raise ValueError(
                    "Для comparison "
                    "отсутствует period."
                )

            payload = compare_financial_companies(
                facts=facts,
                companies=(
                    current_question.company_ids
                ),
                period=period,
                metric=metric,
            )

            return DispatchResult(
                status=DispatchStatus.COMPLETED,
                tool_name="compare_companies",
                parsed_question=current_question,
                payload=payload,
                message=(
                    "Сравнение компаний выполнено."
                ),
            )

        # -------------------------------------------------
        # 9. GROWTH
        # -------------------------------------------------

        if (
            current_question.intent
            == QuestionIntent.GROWTH
        ):
            company_id = (
                current_question.company_ids[0]
            )

            from_period = (
                current_question.from_period
            )

            to_period = (
                current_question.to_period
            )

            if (
                from_period is None
                or to_period is None
            ):
                raise ValueError(
                    "Для growth отсутствуют периоды."
                )

            payload = calculate_financial_growth(
                facts=facts,
                company_id=company_id,
                metric=metric,
                from_period=from_period,
                to_period=to_period,
            )

            return DispatchResult(
                status=DispatchStatus.COMPLETED,
                tool_name="calculate_growth",
                parsed_question=current_question,
                payload=payload,
                message=(
                    "Динамика показателя рассчитана."
                ),
            )

    except (
        ValueError,
        KeyError,
    ) as error:
        return DispatchResult(
            status=DispatchStatus.ERROR,
            tool_name=None,
            parsed_question=current_question,
            payload=None,
            message=str(error),
        )

    return DispatchResult(
        status=DispatchStatus.ERROR,
        tool_name=None,
        parsed_question=current_question,
        payload=None,
        message=(
            "Dispatcher получил "
            "неподдерживаемый intent."
        ),
    )