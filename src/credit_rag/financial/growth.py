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
from credit_rag.financial.temporal_comparability import (
    TemporalComparabilityStatus,
    assess_temporal_comparability,
)
from credit_rag.financial.units import UnitCode


@dataclass(frozen=True)
class GrowthResult:
    """
    Результат расчета динамики финансового показателя.
    """

    company_id: str
    metric: MetricCode
    from_period: str
    to_period: str

    from_value: Decimal
    to_value: Decimal
    unit: UnitCode

    absolute_change: Decimal
    growth_pct: Decimal

    from_source_fact: FinancialFact
    to_source_fact: FinancialFact


def get_single_period_fact(
    facts: Sequence[FinancialFact],
    company_id: str,
    period: str,
    metric: MetricCode,
    standard: FinancialStandard,
) -> FinancialFact:
    """
    Возвращает единственный финансовый факт
    для заданной компании, периода и метрики.
    """
    results = query_facts(
        facts=facts,
        company_id=company_id,
        period=period,
        metric=metric,
        standard=standard,
    )

    if not results:
        raise ValueError(
            f"Не найден показатель {metric.value} "
            f"для {company_id}, период {period}."
        )

    if len(results) > 1:
        raise ValueError(
            f"Найдено несколько значений {metric.value} "
            f"для {company_id}, период {period}."
        )

    return results[0]


def calculate_growth(
    facts: Sequence[FinancialFact],
    company_id: str,
    metric: MetricCode,
    from_period: str,
    to_period: str,
    standard: FinancialStandard = FinancialStandard.IFRS,
) -> GrowthResult:
    """
    Рассчитывает абсолютное и процентное изменение
    финансового показателя между двумя периодами.

    Расчет выполняется только если временная
    сопоставимость показателя подтверждена.
    """

    comparability = assess_temporal_comparability(
        company_id=company_id,
        metric=metric,
        from_period=from_period,
        to_period=to_period,
    )

    if (
        comparability.status
        != TemporalComparabilityStatus.COMPARABLE
    ):
        raise ValueError(
            "Нельзя рассчитать динамику: "
            f"{comparability.status.value}. "
            f"{comparability.message}"
        )

    from_fact = get_single_period_fact(
        facts=facts,
        company_id=company_id,
        period=from_period,
        metric=metric,
        standard=standard,
    )

    to_fact = get_single_period_fact(
        facts=facts,
        company_id=company_id,
        period=to_period,
        metric=metric,
        standard=standard,
    )

    # Для расчета приводим оба значения
    # к единице исходного периода.
    target_unit = from_fact.unit

    normalized_from = normalize_fact_unit(
        fact=from_fact,
        target_unit=target_unit,
    )

    normalized_to = normalize_fact_unit(
        fact=to_fact,
        target_unit=target_unit,
    )

    if normalized_from.value == 0:
        raise ValueError(
            "Нельзя рассчитать процентную динамику: "
            "значение исходного периода равно нулю."
        )

    absolute_change = (
        normalized_to.value
        - normalized_from.value
    )

    growth_pct = (
        absolute_change
        / normalized_from.value
        * Decimal(100)
    )

    return GrowthResult(
        company_id=company_id,
        metric=metric,
        from_period=from_period,
        to_period=to_period,
        from_value=normalized_from.value,
        to_value=normalized_to.value,
        unit=target_unit,
        absolute_change=absolute_change,
        growth_pct=growth_pct,
        from_source_fact=from_fact,
        to_source_fact=to_fact,
    )