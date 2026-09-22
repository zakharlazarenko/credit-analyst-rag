from decimal import Decimal

from credit_rag.financial.calculations import (
    DerivedMetricCode,
    compute_metric,
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
            company_id="TEST",
            period="2025",
            standard=FinancialStandard.IFRS,
            metric=MetricCode.NET_DEBT,
            value=Decimal(600),
            unit=UnitCode.RUB_BILLION,
            doc_id="test_document",
            page=1,
            extraction_method=ExtractionMethod.MANUAL,
            confidence=1.0,
        ),
        FinancialFact(
            company_id="TEST",
            period="2025",
            standard=FinancialStandard.IFRS,
            metric=MetricCode.EBITDA,
            value=Decimal(1500000),
            unit=UnitCode.RUB_MILLION,
            doc_id="test_document",
            page=2,
            extraction_method=ExtractionMethod.MANUAL,
            confidence=1.0,
        ),
        FinancialFact(
            company_id="TEST",
            period="2025",
            standard=FinancialStandard.IFRS,
            metric=MetricCode.OPERATING_CASH_FLOW,
            value=Decimal(1414523),
            unit=UnitCode.RUB_MILLION,
            doc_id="test_document",
            page=3,
            extraction_method=ExtractionMethod.MANUAL,
            confidence=1.0,
        ),
        FinancialFact(
            company_id="TEST",
            period="2025",
            standard=FinancialStandard.IFRS,
            metric=MetricCode.CAPEX,
            value=Decimal("774.550"),
            unit=UnitCode.RUB_BILLION,
            doc_id="test_document",
            page=4,
            extraction_method=ExtractionMethod.MANUAL,
            confidence=1.0,
        ),
    ]


def test_net_debt_to_ebitda_with_mixed_units() -> None:
    result = compute_metric(
        facts=build_test_facts(),
        company_id="TEST",
        period="2025",
        metric=DerivedMetricCode.NET_DEBT_TO_EBITDA,
    )

    assert result.value == Decimal("0.4")
    assert result.unit == "x"

    assert len(result.source_facts) == 2


def test_free_cash_flow_with_mixed_units() -> None:
    result = compute_metric(
        facts=build_test_facts(),
        company_id="TEST",
        period="2025",
        metric=DerivedMetricCode.FREE_CASH_FLOW,
    )

    assert result.value == Decimal(639973)
    assert result.unit == UnitCode.RUB_MILLION

    assert len(result.source_facts) == 2