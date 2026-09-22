from dataclasses import dataclass
from enum import StrEnum

from credit_rag.financial.metrics import MetricCode


class TemporalComparabilityStatus(StrEnum):
    """
    Статус сопоставимости одной метрики
    между двумя отчетными периодами.
    """

    COMPARABLE = "comparable"
    NOT_COMPARABLE = "not_comparable"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class TemporalComparabilityResult:
    """
    Результат проверки временной сопоставимости.
    """

    company_id: str
    metric: MetricCode
    from_period: str
    to_period: str
    status: TemporalComparabilityStatus
    message: str


# Показатели, сопоставимость которых мы уже
# подтвердили по отчетности.
COMPARABLE_METRICS_2024_2025 = {
    "ROSNEFT": {
        MetricCode.REVENUE,
        MetricCode.OPERATING_PROFIT,
        MetricCode.TOTAL_ASSETS,
        MetricCode.TOTAL_EQUITY,
    },

    "TATNEFT": {
        MetricCode.REVENUE,
        MetricCode.OPERATING_PROFIT,
        MetricCode.OPERATING_CASH_FLOW,
        MetricCode.CASH_AND_EQUIVALENTS,
    },
}


def assess_temporal_comparability(
    company_id: str,
    metric: MetricCode,
    from_period: str,
    to_period: str,
) -> TemporalComparabilityResult:
    """
    Проверяет, можно ли напрямую сравнивать
    значение одной метрики между двумя периодами.
    """

    # Пока правила подтверждены только
    # для перехода 2024 -> 2025.
    if (
        from_period != "2024"
        or to_period != "2025"
    ):
        return TemporalComparabilityResult(
            company_id=company_id,
            metric=metric,
            from_period=from_period,
            to_period=to_period,
            status=TemporalComparabilityStatus.UNKNOWN,
            message=(
                "Для этой пары периодов сопоставимость "
                "пока не проверена."
            ),
        )

    # LUKOIL revenue — известный проблемный случай:
    # comparative 2024 в отчете 2025 существенно
    # отличается от значения в отдельном отчете 2024.
    if (
        company_id == "LUKOIL"
        and metric == MetricCode.REVENUE
    ):
        return TemporalComparabilityResult(
            company_id=company_id,
            metric=metric,
            from_period=from_period,
            to_period=to_period,
            status=(
                TemporalComparabilityStatus.NOT_COMPARABLE
            ),
            message=(
                "Выручка LUKOIL за 2024 год в отчетности "
                "2025 года представлена на иной сравнительной "
                "базе. Использовать значение из отдельного "
                "отчета 2024 для прямого YoY-сравнения нельзя."
            ),
        )

    comparable_metrics = (
        COMPARABLE_METRICS_2024_2025.get(
            company_id,
            set(),
        )
    )

    if metric in comparable_metrics:
        return TemporalComparabilityResult(
            company_id=company_id,
            metric=metric,
            from_period=from_period,
            to_period=to_period,
            status=TemporalComparabilityStatus.COMPARABLE,
            message=(
                "Показатель подтвержден как сопоставимый "
                "между периодами."
            ),
        )

    return TemporalComparabilityResult(
        company_id=company_id,
        metric=metric,
        from_period=from_period,
        to_period=to_period,
        status=TemporalComparabilityStatus.UNKNOWN,
        message=(
            "Сопоставимость показателя между этими "
            "периодами пока не подтверждена."
        ),
    )