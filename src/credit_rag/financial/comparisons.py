from collections.abc import Sequence
from dataclasses import dataclass
from decimal import Decimal

from credit_rag.financial.fact_store import query_facts
from credit_rag.financial.metrics import MetricCode
from credit_rag.financial.normalization import normalize_fact_unit
from credit_rag.financial.schemas import (
    FinancialFact,
    FinancialStandard,
)
from credit_rag.financial.units import UnitCode


@dataclass(frozen=True)
class ComparableMetricValue:
    """
    Значение одной метрики одной компании,
    приведенное к общей единице измерения.
    """

    company_id: str
    period: str
    metric: MetricCode
    value: Decimal
    unit: UnitCode
    source_fact: FinancialFact


@dataclass(frozen=True)
class CompanyComparison:
    """
    Результат сравнения одного финансового показателя
    между несколькими компаниями.
    """

    metric: MetricCode
    period: str
    unit: UnitCode
    values: tuple[ComparableMetricValue, ...]
    missing_companies: tuple[str, ...]


def compare_companies(
    facts: Sequence[FinancialFact],
    companies: Sequence[str],
    period: str,
    metric: MetricCode,
    target_unit: UnitCode = UnitCode.RUB_MILLION,
    standard: FinancialStandard = FinancialStandard.IFRS,
) -> CompanyComparison:
    """
    Сравнивает один финансовый показатель
    между несколькими компаниями.

    Для каждой компании:
    1. Находит исходный FinancialFact.
    2. Проверяет, что факт единственный.
    3. Приводит значение к общей денежной единице.
    4. Сохраняет исходный факт для provenance.

    Если показатель у компании отсутствует,
    компания попадает в missing_companies.
    """
    comparable_values: list[ComparableMetricValue] = []
    missing_companies: list[str] = []

    for company_id in companies:
        company_facts = query_facts(
            facts=facts,
            company_id=company_id,
            period=period,
            metric=metric,
            standard=standard,
        )

        if not company_facts:
            missing_companies.append(company_id)
            continue

        if len(company_facts) > 1:
            raise ValueError(
                f"Найдено несколько значений "
                f"{metric.value} для "
                f"{company_id}, период {period}."
            )

        source_fact = company_facts[0]

        normalized_fact = normalize_fact_unit(
            fact=source_fact,
            target_unit=target_unit,
        )

        comparable_values.append(
            ComparableMetricValue(
                company_id=company_id,
                period=period,
                metric=metric,
                value=normalized_fact.value,
                unit=target_unit,
                source_fact=source_fact,
            )
        )

    comparable_values.sort(
        key=lambda item: item.value,
        reverse=True,
    )

    return CompanyComparison(
        metric=metric,
        period=period,
        unit=target_unit,
        values=tuple(comparable_values),
        missing_companies=tuple(missing_companies),
    )