from decimal import Decimal

from credit_rag.financial.fact_store import (
    load_facts,
    query_facts,
    save_facts,
)
from credit_rag.financial.metrics import MetricCode
from credit_rag.financial.schemas import (
    ExtractionMethod,
    FinancialFact,
    FinancialStandard,
)
from credit_rag.financial.units import UnitCode


def test_save_load_and_query_facts(tmp_path) -> None:
    facts = [
        FinancialFact(
            company_id="LUKOIL",
            period="2025",
            standard=FinancialStandard.IFRS,
            metric=MetricCode.REVENUE,
            value=Decimal(100),
            unit=UnitCode.RUB,
            doc_id="test_lukoil_ifrs_2025",
            page=10,
            extraction_method=ExtractionMethod.MANUAL,
            confidence=1.0,
        ),
        FinancialFact(
            company_id="LUKOIL",
            period="2025",
            standard=FinancialStandard.IFRS,
            metric=MetricCode.EBITDA,
            value=Decimal(25),
            unit=UnitCode.RUB,
            doc_id="test_lukoil_ifrs_2025",
            page=11,
            extraction_method=ExtractionMethod.MANUAL,
            confidence=1.0,
        ),
        FinancialFact(
            company_id="ROSNEFT",
            period="2025",
            standard=FinancialStandard.IFRS,
            metric=MetricCode.REVENUE,
            value=Decimal(200),
            unit=UnitCode.RUB,
            doc_id="test_rosneft_ifrs_2025",
            page=12,
            extraction_method=ExtractionMethod.MANUAL,
            confidence=1.0,
        ),
    ]

    path = tmp_path / "financial_facts.jsonl"

    save_facts(
        facts=facts,
        path=path,
    )

    loaded_facts = load_facts(path)

    assert len(loaded_facts) == 3

    results = query_facts(
        facts=loaded_facts,
        company_id="LUKOIL",
        period="2025",
        metric="выручка",
        standard=FinancialStandard.IFRS,
    )

    assert len(results) == 1

    fact = results[0]

    assert fact.company_id == "LUKOIL"
    assert fact.period == "2025"
    assert fact.metric == MetricCode.REVENUE
    assert fact.value == Decimal(100)
    assert fact.unit == UnitCode.RUB
    assert fact.doc_id == "test_lukoil_ifrs_2025"
    assert fact.page == 10