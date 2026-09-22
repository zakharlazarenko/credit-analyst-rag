from decimal import Decimal

from credit_rag.financial.metrics import MetricCode
from credit_rag.financial.normalization import (
    normalize_fact_unit,
)
from credit_rag.financial.schemas import (
    ExtractionMethod,
    FinancialFact,
    FinancialStandard,
)
from credit_rag.financial.units import UnitCode


def test_normalization_keeps_same_unit() -> None:
    fact = FinancialFact(
        company_id="LUKOIL",
        period="2025",
        standard=FinancialStandard.IFRS,
        metric=MetricCode.REVENUE,
        value=Decimal(3767768),
        unit=UnitCode.RUB_MILLION,
        doc_id="lukoil_ifrs_2025",
        page=7,
        extraction_method=ExtractionMethod.TABLE,
        confidence=0.90,
    )

    normalized = normalize_fact_unit(
        fact=fact,
        target_unit=UnitCode.RUB_MILLION,
    )

    assert normalized.value == Decimal(
        3767768
    )

    assert (
        normalized.unit
        == UnitCode.RUB_MILLION
    )


def test_normalization_billion_to_million() -> None:
    fact = FinancialFact(
        company_id="ROSNEFT",
        period="2025",
        standard=FinancialStandard.IFRS,
        metric=MetricCode.REVENUE,
        value=Decimal(8236),
        unit=UnitCode.RUB_BILLION,
        doc_id="rosneft_ifrs_2025",
        page=6,
        extraction_method=ExtractionMethod.TABLE,
        confidence=0.90,
    )

    normalized = normalize_fact_unit(
        fact=fact,
        target_unit=UnitCode.RUB_MILLION,
    )

    assert normalized.value == Decimal(
        8236000
    )

    assert (
        normalized.unit
        == UnitCode.RUB_MILLION
    )