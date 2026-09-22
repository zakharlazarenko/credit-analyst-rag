from decimal import Decimal

from credit_rag.financial.metrics import MetricCode
from credit_rag.financial.schemas import (
    ExtractionMethod,
    FinancialFact,
    FinancialStandard,
)
from credit_rag.financial.units import UnitCode


def test_financial_fact_creation() -> None:
    fact = FinancialFact(
        company_id="LUKOIL",
        period="2025",
        standard=FinancialStandard.IFRS,
        metric="revenue",
        value=Decimal(8500000000000),
        unit="RUB",
        doc_id="lukoil_ifrs_2025",
        page=12,
        extraction_method=ExtractionMethod.MANUAL,
        confidence=1.0,
    )

    assert fact.company_id == "LUKOIL"
    assert fact.period == "2025"
    assert fact.standard == FinancialStandard.IFRS

    assert fact.metric == MetricCode.REVENUE
    assert fact.value == Decimal(8500000000000)
    assert fact.unit == UnitCode.RUB

    assert fact.doc_id == "lukoil_ifrs_2025"
    assert fact.page == 12

    assert (
        fact.extraction_method
        == ExtractionMethod.MANUAL
    )

    assert fact.confidence == 1.0