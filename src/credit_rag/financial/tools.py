from collections.abc import Sequence
from typing import Any

from credit_rag.financial.calculations import (
    DerivedMetricCode,
    compute_metric,
)
from credit_rag.financial.comparability import (
    assess_comparability,
)
from credit_rag.financial.comparisons import compare_companies
from credit_rag.financial.fact_store import query_facts
from credit_rag.financial.growth import calculate_growth
from credit_rag.financial.metrics import MetricCode
from credit_rag.financial.schemas import (
    FinancialFact,
    FinancialStandard,
)
from credit_rag.financial.units import UnitCode


def financial_fact_to_dict(
    fact: FinancialFact,
) -> dict[str, Any]:
    """
    Преобразует FinancialFact
    в простой сериализуемый словарь.
    """
    return {
        "company_id": fact.company_id,
        "period": fact.period,
        "standard": fact.standard.value,
        "metric": fact.metric.value,
        "value": str(fact.value),
        "unit": fact.unit.value,
        "doc_id": fact.doc_id,
        "page": fact.page,
        "extraction_method": fact.extraction_method.value,
        "confidence": fact.confidence,
    }


def query_financial_facts(
    facts: Sequence[FinancialFact],
    company_id: str,
    period: str,
    metric: str,
    standard: FinancialStandard = FinancialStandard.IFRS,
) -> dict[str, Any]:
    """
    Tool-level интерфейс для поиска
    исходных финансовых фактов.
    """
    metric_code = MetricCode(metric)

    results = query_facts(
        facts=facts,
        company_id=company_id,
        period=period,
        metric=metric_code,
        standard=standard,
    )

    return {
        "tool": "query_facts",
        "company_id": company_id,
        "period": period,
        "metric": metric_code.value,
        "count": len(results),
        "facts": [
            financial_fact_to_dict(fact)
            for fact in results
        ],
    }


def compute_financial_metric(
    facts: Sequence[FinancialFact],
    company_id: str,
    period: str,
    metric: str,
    standard: FinancialStandard = FinancialStandard.IFRS,
) -> dict[str, Any]:
    """
    Tool-level интерфейс для расчета
    производной финансовой метрики.
    """
    metric_code = DerivedMetricCode(metric)

    result = compute_metric(
        facts=facts,
        company_id=company_id,
        period=period,
        metric=metric_code,
        standard=standard,
    )

    return {
        "tool": "compute_metric",
        "company_id": result.company_id,
        "period": result.period,
        "metric": result.metric.value,
        "value": str(result.value),
        "unit": str(result.unit),
        "source_facts": [
            financial_fact_to_dict(fact)
            for fact in result.source_facts
        ],
    }


def compare_financial_companies(
    facts: Sequence[FinancialFact],
    companies: Sequence[str],
    period: str,
    metric: str,
    target_unit: UnitCode = UnitCode.RUB_MILLION,
    standard: FinancialStandard = FinancialStandard.IFRS,
) -> dict[str, Any]:
    """
    Tool-level интерфейс для сравнения
    одной метрики между компаниями.

    Помимо числового сравнения возвращает
    оценку методологической сопоставимости.
    """
    metric_code = MetricCode(metric)

    result = compare_companies(
        facts=facts,
        companies=companies,
        period=period,
        metric=metric_code,
        target_unit=target_unit,
        standard=standard,
    )

    comparability = assess_comparability(
        companies=tuple(companies),
        metric=metric_code,
    )

    return {
        "tool": "compare_companies",
        "period": result.period,
        "metric": result.metric.value,
        "unit": result.unit.value,

        "comparability": {
            "status": comparability.status.value,
            "message": comparability.message,
        },

        "values": [
            {
                "company_id": item.company_id,
                "value": str(item.value),
                "unit": item.unit.value,
                "source_fact": financial_fact_to_dict(
                    item.source_fact
                ),
            }
            for item in result.values
        ],

        "missing_companies": list(
            result.missing_companies
        ),
    }


def calculate_financial_growth(
    facts: Sequence[FinancialFact],
    company_id: str,
    metric: str,
    from_period: str,
    to_period: str,
    standard: FinancialStandard = FinancialStandard.IFRS,
) -> dict[str, Any]:
    """
    Tool-level интерфейс для безопасного
    расчета динамики показателя.
    """
    metric_code = MetricCode(metric)

    result = calculate_growth(
        facts=facts,
        company_id=company_id,
        metric=metric_code,
        from_period=from_period,
        to_period=to_period,
        standard=standard,
    )

    return {
        "tool": "calculate_growth",
        "company_id": result.company_id,
        "metric": result.metric.value,
        "from_period": result.from_period,
        "to_period": result.to_period,
        "from_value": str(result.from_value),
        "to_value": str(result.to_value),
        "unit": result.unit.value,
        "absolute_change": str(
            result.absolute_change
        ),
        "growth_pct": str(
            result.growth_pct
        ),
        "sources": {
            "from": financial_fact_to_dict(
                result.from_source_fact
            ),
            "to": financial_fact_to_dict(
                result.to_source_fact
            ),
        },
    }