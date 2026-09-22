from decimal import Decimal

from credit_rag.assistant.dispatcher import (
    DispatchStatus,
    dispatch_question,
)
from credit_rag.assistant.routing import (
    ParsedQuestion,
    QuestionIntent,
)
from credit_rag.financial.metrics import MetricCode
from credit_rag.financial.schemas import (
    ExtractionMethod,
    FinancialFact,
    FinancialStandard,
)
from credit_rag.financial.units import UnitCode


def build_test_facts() -> list[FinancialFact]:
    return [
        FinancialFact(
            company_id="ROSNEFT",
            period="2025",
            standard=FinancialStandard.IFRS,
            metric=MetricCode.REVENUE,
            value=Decimal(8236),
            unit=UnitCode.RUB_BILLION,
            doc_id="rosneft_ifrs_2025",
            page=6,
            extraction_method=ExtractionMethod.TABLE,
            confidence=1.0,
        ),
        FinancialFact(
            company_id="LUKOIL",
            period="2025",
            standard=FinancialStandard.IFRS,
            metric=MetricCode.NET_DEBT,
            value=Decimal(-225803),
            unit=UnitCode.RUB_MILLION,
            doc_id="lukoil_ifrs_2025",
            page=53,
            extraction_method=ExtractionMethod.TABLE,
            confidence=1.0,
        ),
        FinancialFact(
            company_id="LUKOIL",
            period="2025",
            standard=FinancialStandard.IFRS,
            metric=MetricCode.EBITDA,
            value=Decimal(892086),
            unit=UnitCode.RUB_MILLION,
            doc_id="lukoil_ifrs_2025",
            page=46,
            extraction_method=ExtractionMethod.TABLE,
            confidence=1.0,
        ),
    ]


def fake_qualitative_handler(
    question: str,
    parsed: ParsedQuestion,
) -> dict:
    return {
        "answer": "Тестовый grounded answer.",
        "question": question,
        "company_id": parsed.company_ids[0],
        "period": parsed.period,
    }


def test_dispatch_fact() -> None:
    parsed = ParsedQuestion(
        intent=QuestionIntent.FACT,
        company_ids=("ROSNEFT",),
        metric="revenue",
        period="2025",
        from_period=None,
        to_period=None,
        reason="Test.",
    )

    result = dispatch_question(
        question="Какая выручка Роснефти?",
        parsed=parsed,
        facts=build_test_facts(),
        qualitative_handler=(
            fake_qualitative_handler
        ),
    )

    assert result.status == DispatchStatus.COMPLETED
    assert result.tool_name == "query_facts"
    assert result.payload is not None
    assert result.payload["count"] == 1


def test_dispatch_derived_metric() -> None:
    parsed = ParsedQuestion(
        intent=QuestionIntent.DERIVED_METRIC,
        company_ids=("LUKOIL",),
        metric="net_debt_to_ebitda",
        period="2025",
        from_period=None,
        to_period=None,
        reason="Test.",
    )

    result = dispatch_question(
        question="Какой Net Debt / EBITDA?",
        parsed=parsed,
        facts=build_test_facts(),
        qualitative_handler=(
            fake_qualitative_handler
        ),
    )

    assert result.status == DispatchStatus.COMPLETED
    assert result.tool_name == "compute_metric"
    assert result.payload is not None

    assert (
        result.payload["metric"]
        == "net_debt_to_ebitda"
    )


def test_dispatch_qualitative() -> None:
    parsed = ParsedQuestion(
        intent=QuestionIntent.QUALITATIVE,
        company_ids=("LUKOIL",),
        metric=None,
        period="2025",
        from_period=None,
        to_period=None,
        reason="Test.",
    )

    result = dispatch_question(
        question="Какие риски описывает ЛУКОЙЛ?",
        parsed=parsed,
        facts=build_test_facts(),
        qualitative_handler=(
            fake_qualitative_handler
        ),
    )

    assert result.status == DispatchStatus.COMPLETED
    assert result.tool_name == "retrieve_docs"
    assert result.payload is not None

    assert (
        result.payload["answer"]
        == "Тестовый grounded answer."
    )


def test_dispatch_qualitative_missing_period() -> None:
    parsed = ParsedQuestion(
        intent=QuestionIntent.QUALITATIVE,
        company_ids=("LUKOIL",),
        metric=None,
        period=None,
        from_period=None,
        to_period=None,
        reason="Test.",
    )

    result = dispatch_question(
        question="Какие риски описывает ЛУКОЙЛ?",
        parsed=parsed,
        facts=build_test_facts(),
        qualitative_handler=(
            fake_qualitative_handler
        ),
    )

    assert (
        result.status
        == DispatchStatus.NEEDS_CLARIFICATION
    )

    assert result.tool_name is None


def test_dispatch_unknown() -> None:
    parsed = ParsedQuestion(
        intent=QuestionIntent.UNKNOWN,
        company_ids=("LUKOIL",),
        metric=None,
        period=None,
        from_period=None,
        to_period=None,
        reason="Test.",
    )

    result = dispatch_question(
        question="Стоит ли выдавать кредит?",
        parsed=parsed,
        facts=build_test_facts(),
        qualitative_handler=(
            fake_qualitative_handler
        ),
    )

    assert result.status == DispatchStatus.UNSUPPORTED
    assert result.tool_name is None
    assert result.payload is None