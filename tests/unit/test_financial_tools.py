from decimal import Decimal

from credit_rag.financial.metrics import MetricCode
from credit_rag.financial.schemas import (
    ExtractionMethod,
    FinancialFact,
    FinancialStandard,
)
from credit_rag.financial.tools import (
    calculate_financial_growth,
    compare_financial_companies,
    compute_financial_metric,
    query_financial_facts,
)
from credit_rag.financial.units import UnitCode


def build_test_facts() -> list[FinancialFact]:
    return [
        FinancialFact(
            company_id="LUKOIL",
            period="2025",
            standard=FinancialStandard.IFRS,
            metric=MetricCode.REVENUE,
            value=Decimal(3767768),
            unit=UnitCode.RUB_MILLION,
            doc_id="lukoil_ifrs_2025",
            page=7,
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
            company_id="TATNEFT",
            period="2025",
            standard=FinancialStandard.IFRS,
            metric=MetricCode.REVENUE,
            value=Decimal(1818134),
            unit=UnitCode.RUB_MILLION,
            doc_id="tatneft_ifrs_2025",
            page=9,
            extraction_method=ExtractionMethod.TABLE,
            confidence=1.0,
        ),
    ]


def test_query_financial_facts() -> None:
    result = query_financial_facts(
        facts=build_test_facts(),
        company_id="LUKOIL",
        period="2025",
        metric="revenue",
    )

    assert result["tool"] == "query_facts"
    assert result["count"] == 1

    fact = result["facts"][0]

    assert fact["company_id"] == "LUKOIL"
    assert fact["metric"] == "revenue"
    assert fact["value"] == "3767768"
    assert fact["unit"] == "RUB_MILLION"
    assert fact["page"] == 7


def test_compute_financial_metric() -> None:
    result = compute_financial_metric(
        facts=build_test_facts(),
        company_id="LUKOIL",
        period="2025",
        metric="net_debt_to_ebitda",
    )

    assert result["tool"] == "compute_metric"
    assert result["metric"] == "net_debt_to_ebitda"
    assert result["unit"] == "x"

    expected = (
        Decimal(-225803)
        / Decimal(892086)
    )

    assert Decimal(result["value"]) == expected
    assert len(result["source_facts"]) == 2


def test_compare_financial_companies() -> None:
    result = compare_financial_companies(
        facts=build_test_facts(),
        companies=(
            "LUKOIL",
            "ROSNEFT",
            "TATNEFT",
        ),
        period="2025",
        metric="revenue",
    )

    assert result["tool"] == "compare_companies"
    assert result["unit"] == "RUB_MILLION"
    assert len(result["values"]) == 3
    assert result["missing_companies"] == []

    assert (
        result["comparability"]["status"]
        == "caution"
    )


def test_calculate_financial_growth() -> None:
    result = calculate_financial_growth(
        facts=build_test_facts(),
        company_id="ROSNEFT",
        metric="revenue",
        from_period="2024",
        to_period="2025",
    )

    assert result["tool"] == "calculate_growth"
    assert result["from_value"] == "10139"
    assert result["to_value"] == "8236"
    assert result["absolute_change"] == "-1903"

    expected_growth = (
        Decimal(-1903)
        / Decimal(10139)
        * Decimal(100)
    )

    assert (
        Decimal(result["growth_pct"])
        == expected_growth
    )