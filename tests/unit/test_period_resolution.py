from decimal import Decimal

from credit_rag.assistant.resolution import (
    ResolutionStatus,
    resolve_growth_periods,
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
            company_id="TATNEFT",
            period="2024",
            standard=FinancialStandard.IFRS,
            metric=MetricCode.OPERATING_CASH_FLOW,
            value=Decimal(425129),
            unit=UnitCode.RUB_MILLION,
            doc_id="tatneft_ifrs_2024",
            page=13,
            extraction_method=ExtractionMethod.TABLE,
            confidence=1.0,
        ),
        FinancialFact(
            company_id="TATNEFT",
            period="2025",
            standard=FinancialStandard.IFRS,
            metric=MetricCode.OPERATING_CASH_FLOW,
            value=Decimal(261795),
            unit=UnitCode.RUB_MILLION,
            doc_id="tatneft_ifrs_2025",
            page=13,
            extraction_method=ExtractionMethod.TABLE,
            confidence=1.0,
        ),
        FinancialFact(
            company_id="ROSNEFT",
            period="2024",
            standard=FinancialStandard.IFRS,
            metric=MetricCode.REVENUE,
            value=Decimal(10139),
            unit=UnitCode.RUB_BILLION,
            doc_id="rosneft_ifrs_2024",
            page=6,
            extraction_method=ExtractionMethod.TABLE,
            confidence=1.0,
        ),
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
            period="2024",
            standard=FinancialStandard.IFRS,
            metric=MetricCode.EBITDA,
            value=Decimal(1785263),
            unit=UnitCode.RUB_MILLION,
            doc_id="lukoil_ifrs_2024",
            page=42,
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


def test_resolve_both_missing_periods() -> None:
    parsed = ParsedQuestion(
        intent=QuestionIntent.GROWTH,
        company_ids=("TATNEFT",),
        metric="operating_cash_flow",
        period=None,
        from_period=None,
        to_period=None,
        reason="Test.",
    )

    result = resolve_growth_periods(
        parsed=parsed,
        facts=build_test_facts(),
    )

    assert result.status == ResolutionStatus.RESOLVED

    assert (
        result.parsed_question.from_period
        == "2024"
    )

    assert (
        result.parsed_question.to_period
        == "2025"
    )


def test_resolve_missing_to_period() -> None:
    parsed = ParsedQuestion(
        intent=QuestionIntent.GROWTH,
        company_ids=("ROSNEFT",),
        metric="revenue",
        period=None,
        from_period="2024",
        to_period=None,
        reason="Test.",
    )

    result = resolve_growth_periods(
        parsed=parsed,
        facts=build_test_facts(),
    )

    assert result.status == ResolutionStatus.RESOLVED

    assert (
        result.parsed_question.from_period
        == "2024"
    )

    assert (
        result.parsed_question.to_period
        == "2025"
    )


def test_unknown_comparability_is_not_resolved() -> None:
    parsed = ParsedQuestion(
        intent=QuestionIntent.GROWTH,
        company_ids=("LUKOIL",),
        metric="ebitda",
        period=None,
        from_period=None,
        to_period=None,
        reason="Test.",
    )

    result = resolve_growth_periods(
        parsed=parsed,
        facts=build_test_facts(),
    )

    assert (
        result.status
        == ResolutionStatus.UNRESOLVED
    )

    assert (
        result.parsed_question.from_period
        is None
    )

    assert (
        result.parsed_question.to_period
        is None
    )


def test_complete_growth_needs_no_resolution() -> None:
    parsed = ParsedQuestion(
        intent=QuestionIntent.GROWTH,
        company_ids=("ROSNEFT",),
        metric="revenue",
        period=None,
        from_period="2024",
        to_period="2025",
        reason="Test.",
    )

    result = resolve_growth_periods(
        parsed=parsed,
        facts=build_test_facts(),
    )

    assert (
        result.status
        == ResolutionStatus.NOT_NEEDED
    )

    assert (
        result.parsed_question.from_period
        == "2024"
    )

    assert (
        result.parsed_question.to_period
        == "2025"
    )