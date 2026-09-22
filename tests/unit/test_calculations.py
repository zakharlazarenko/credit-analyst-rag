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


def test_compute_net_debt_to_ebitda() -> None:
    facts = [
        FinancialFact(
            company_id="LUKOIL",
            period="2025",
            standard=FinancialStandard.IFRS,
            metric=MetricCode.NET_DEBT,
            value=Decimal(600),
            unit=UnitCode.RUB_BILLION,
            doc_id="test_lukoil_ifrs_2025",
            page=20,
            extraction_method=ExtractionMethod.MANUAL,
            confidence=1.0,
        ),
        FinancialFact(
            company_id="LUKOIL",
            period="2025",
            standard=FinancialStandard.IFRS,
            metric=MetricCode.EBITDA,
            value=Decimal(1500),
            unit=UnitCode.RUB_BILLION,
            doc_id="test_lukoil_ifrs_2025",
            page=15,
            extraction_method=ExtractionMethod.MANUAL,
            confidence=1.0,
        ),
    ]

    result = compute_metric(
        facts=facts,
        company_id="LUKOIL",
        period="2025",
        metric=DerivedMetricCode.NET_DEBT_TO_EBITDA,
        standard=FinancialStandard.IFRS,
    )

    assert result.company_id == "LUKOIL"
    assert result.period == "2025"
    assert result.metric == DerivedMetricCode.NET_DEBT_TO_EBITDA

    assert result.value == Decimal("0.4")
    assert result.unit == "x"

    assert len(result.source_facts) == 2

    source_metrics = {
        fact.metric
        for fact in result.source_facts
    }

    assert source_metrics == {
        MetricCode.NET_DEBT,
        MetricCode.EBITDA,
    }