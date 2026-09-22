from credit_rag.assistant.answer_formatter import (
    format_decimal,
    format_dispatch_result,
    format_value,
)
from credit_rag.assistant.dispatcher import (
    DispatchResult,
    DispatchStatus,
)
from credit_rag.assistant.routing import (
    ParsedQuestion,
    QuestionIntent,
)


def test_format_decimal() -> None:
    assert (
        format_decimal("8236")
        == "8 236"
    )

    assert (
        format_decimal(
            "18.769",
            decimal_places=2,
        )
        == "18,77"
    )


def test_format_value_ratio() -> None:
    assert (
        format_value(
            value="-0.253",
            unit="x",
            decimal_places=2,
        )
        == "-0,25x"
    )


def test_format_fact_dispatch_result() -> None:
    parsed = ParsedQuestion(
        intent=QuestionIntent.FACT,
        company_ids=("ROSNEFT",),
        metric="revenue",
        period="2025",
        from_period=None,
        to_period=None,
        reason="Test.",
    )

    result = DispatchResult(
        status=DispatchStatus.COMPLETED,
        tool_name="query_facts",
        parsed_question=parsed,
        payload={
            "tool": "query_facts",
            "company_id": "ROSNEFT",
            "period": "2025",
            "metric": "revenue",
            "count": 1,
            "facts": [
                {
                    "company_id": "ROSNEFT",
                    "period": "2025",
                    "standard": "IFRS",
                    "metric": "revenue",
                    "value": "8236",
                    "unit": "RUB_BILLION",
                    "doc_id": "rosneft_ifrs_2025",
                    "page": 6,
                    "extraction_method": "table",
                    "confidence": 1.0,
                }
            ],
        },
        message="Финансовый факт найден.",
    )

    answer = format_dispatch_result(
        result
    )

    assert (
        "Выручка Роснефти за 2025 год "
        "составила 8 236 млрд руб."
        in answer
    )

    assert (
        "[Роснефть, МСФО 2025, стр. 6]"
        in answer
    )


def test_format_missing_period_clarification() -> None:
    parsed = ParsedQuestion(
        intent=QuestionIntent.FACT,
        company_ids=("ROSNEFT",),
        metric="revenue",
        period=None,
        from_period=None,
        to_period=None,
        reason="Test.",
    )

    result = DispatchResult(
        status=DispatchStatus.NEEDS_CLARIFICATION,
        tool_name=None,
        parsed_question=parsed,
        payload=None,
        message="Missing period.",
    )

    assert format_dispatch_result(
        result
    ) == (
        "Уточните, пожалуйста, год "
        "для выполнения запроса."
    )


def test_format_unknown_request() -> None:
    parsed = ParsedQuestion(
        intent=QuestionIntent.UNKNOWN,
        company_ids=(),
        metric=None,
        period=None,
        from_period=None,
        to_period=None,
        reason="Test.",
    )

    result = DispatchResult(
        status=DispatchStatus.UNSUPPORTED,
        tool_name=None,
        parsed_question=parsed,
        payload=None,
        message="Unsupported.",
    )

    assert format_dispatch_result(
        result
    ) == (
        "Этот запрос пока нельзя выполнить "
        "доступными инструментами ассистента."
    )