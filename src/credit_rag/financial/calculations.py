from collections.abc import Sequence
from dataclasses import dataclass
from decimal import Decimal
from enum import StrEnum

from credit_rag.financial.fact_store import query_facts
from credit_rag.financial.metrics import MetricCode
from credit_rag.financial.schemas import (
    FinancialFact,
    FinancialStandard,
)
from credit_rag.financial.units import (
    UnitCode,
    convert_monetary_value,
)


class DerivedMetricCode(StrEnum):
    """
    Канонические коды рассчитываемых финансовых показателей.
    """

    NET_DEBT_TO_EBITDA = "net_debt_to_ebitda"
    FREE_CASH_FLOW = "free_cash_flow_calculated"


@dataclass(frozen=True)
class ComputedMetric:
    """
    Представляет рассчитанный финансовый показатель.
    """

    company_id: str
    period: str
    metric: DerivedMetricCode
    value: Decimal
    unit: UnitCode | str
    source_facts: tuple[FinancialFact, ...]


def get_single_fact(
    facts: Sequence[FinancialFact],
    company_id: str,
    period: str,
    metric: MetricCode,
    standard: FinancialStandard,
) -> FinancialFact:
    """
    Возвращает единственный финансовый факт для расчета.

    Если факт отсутствует или найдено несколько подходящих фактов,
    расчет не выполняется.
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
            f"Найдено несколько значений показателя {metric.value} "
            f"для {company_id}, период {period}."
        )

    return results[0]


def compute_net_debt_to_ebitda(
    facts: Sequence[FinancialFact],
    company_id: str,
    period: str,
    standard: FinancialStandard,
) -> ComputedMetric:
    """
    Рассчитывает отношение чистого долга к EBITDA.

    Перед расчетом EBITDA автоматически приводится
    к единице измерения чистого долга.
    """
    net_debt = get_single_fact(
        facts=facts,
        company_id=company_id,
        period=period,
        metric=MetricCode.NET_DEBT,
        standard=standard,
    )

    ebitda = get_single_fact(
        facts=facts,
        company_id=company_id,
        period=period,
        metric=MetricCode.EBITDA,
        standard=standard,
    )

    ebitda_value = convert_monetary_value(
        value=ebitda.value,
        source_unit=ebitda.unit,
        target_unit=net_debt.unit,
    )

    if ebitda_value == 0:
        raise ValueError(
            "Нельзя рассчитать Net Debt / EBITDA: "
            "EBITDA равна нулю."
        )

    value = (
        net_debt.value
        / ebitda_value
    )

    return ComputedMetric(
        company_id=company_id,
        period=period,
        metric=DerivedMetricCode.NET_DEBT_TO_EBITDA,
        value=value,
        unit="x",
        source_facts=(
            net_debt,
            ebitda,
        ),
    )


def compute_free_cash_flow(
    facts: Sequence[FinancialFact],
    company_id: str,
    period: str,
    standard: FinancialStandard,
) -> ComputedMetric:
    """
    Рассчитывает стандартизированный свободный денежный поток.

    Формула:
    Free Cash Flow = Operating Cash Flow - CAPEX.

    Перед расчетом CAPEX автоматически приводится
    к единице измерения операционного денежного потока.
    """
    operating_cash_flow = get_single_fact(
        facts=facts,
        company_id=company_id,
        period=period,
        metric=MetricCode.OPERATING_CASH_FLOW,
        standard=standard,
    )

    capex = get_single_fact(
        facts=facts,
        company_id=company_id,
        period=period,
        metric=MetricCode.CAPEX,
        standard=standard,
    )

    capex_value = convert_monetary_value(
        value=capex.value,
        source_unit=capex.unit,
        target_unit=operating_cash_flow.unit,
    )

    value = (
        operating_cash_flow.value
        - capex_value
    )

    return ComputedMetric(
        company_id=company_id,
        period=period,
        metric=DerivedMetricCode.FREE_CASH_FLOW,
        value=value,
        unit=operating_cash_flow.unit,
        source_facts=(
            operating_cash_flow,
            capex,
        ),
    )


def compute_metric(
    facts: Sequence[FinancialFact],
    company_id: str,
    period: str,
    metric: DerivedMetricCode,
    standard: FinancialStandard = FinancialStandard.IFRS,
) -> ComputedMetric:
    """
    Рассчитывает производный финансовый показатель
    по выбранному каноническому коду.
    """
    if metric == DerivedMetricCode.NET_DEBT_TO_EBITDA:
        return compute_net_debt_to_ebitda(
            facts=facts,
            company_id=company_id,
            period=period,
            standard=standard,
        )

    if metric == DerivedMetricCode.FREE_CASH_FLOW:
        return compute_free_cash_flow(
            facts=facts,
            company_id=company_id,
            period=period,
            standard=standard,
        )

    raise ValueError(
        f"Расчет показателя {metric.value} пока не реализован."
    )