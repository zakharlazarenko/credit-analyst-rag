from dataclasses import dataclass
from enum import StrEnum

from credit_rag.financial.metrics import MetricCode


class ComparabilityStatus(StrEnum):
    """
    Уровень методологической сопоставимости показателей.
    """

    COMPARABLE = "comparable"
    CAUTION = "caution"
    NOT_COMPARABLE = "not_comparable"


@dataclass(frozen=True)
class MetricSemanticProfile:
    """
    Описывает экономический смысл показателя
    в конкретном источнике.
    """

    company_id: str
    metric: MetricCode
    source_label: str
    scope: str


@dataclass(frozen=True)
class ComparabilityResult:
    """
    Результат проверки методологической сопоставимости.
    """

    metric: MetricCode
    status: ComparabilityStatus
    message: str


REVENUE_PROFILES = {
    "LUKOIL": MetricSemanticProfile(
        company_id="LUKOIL",
        metric=MetricCode.REVENUE,
        source_label="revenue",
        scope="group_revenue",
    ),

    "ROSNEFT": MetricSemanticProfile(
        company_id="ROSNEFT",
        metric=MetricCode.REVENUE,
        source_label=(
            "итого выручка от реализации и доход "
            "от ассоциированных организаций "
            "и совместных предприятий"
        ),
        scope="revenue_plus_associates_income",
    ),

    "TATNEFT": MetricSemanticProfile(
        company_id="TATNEFT",
        metric=MetricCode.REVENUE,
        source_label=(
            "выручка от реализации "
            "(без финансовых услуг)"
        ),
        scope="revenue_excluding_financial_services",
    ),
}


def assess_comparability(
    companies: tuple[str, ...],
    metric: MetricCode,
) -> ComparabilityResult:
    """
    Оценивает методологическую сопоставимость
    одного показателя между компаниями.
    """
    if metric != MetricCode.REVENUE:
        return ComparabilityResult(
            metric=metric,
            status=ComparabilityStatus.CAUTION,
            message=(
                "Методологическая сопоставимость "
                "этого показателя пока не описана."
            ),
        )

    profiles = [
        REVENUE_PROFILES[company_id]
        for company_id in companies
        if company_id in REVENUE_PROFILES
    ]

    scopes = {
        profile.scope
        for profile in profiles
    }

    if len(scopes) == 1:
        return ComparabilityResult(
            metric=metric,
            status=ComparabilityStatus.COMPARABLE,
            message=(
                "Показатели имеют одинаковый "
                "экономический охват."
            ),
        )

    return ComparabilityResult(
        metric=metric,
        status=ComparabilityStatus.CAUTION,
        message=(
            "Значения приведены к одной денежной единице, "
            "но исходные определения показателя различаются. "
            "Прямое ранжирование требует методологической оговорки."
        ),
    )