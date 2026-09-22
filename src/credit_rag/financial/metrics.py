import re
from dataclasses import dataclass
from enum import StrEnum


class MetricCode(StrEnum):
    """
    Канонические коды финансовых показателей.
    """

    REVENUE = "revenue"
    EBITDA = "ebitda"
    ADJUSTED_EBITDA = "adjusted_ebitda"
    OPERATING_PROFIT = "operating_profit"
    NET_INCOME = "net_income"

    TOTAL_ASSETS = "total_assets"
    TOTAL_EQUITY = "total_equity"

    TOTAL_DEBT = "total_debt"
    CASH_AND_EQUIVALENTS = "cash_and_equivalents"
    NET_DEBT = "net_debt"

    CAPEX = "capex"
    OPERATING_CASH_FLOW = "operating_cash_flow"
    FREE_CASH_FLOW = "free_cash_flow"

    INTEREST_EXPENSE = "interest_expense"
    DIVIDENDS = "dividends"


@dataclass(frozen=True)
class MetricDefinition:
    """
    Описывает канонический финансовый показатель и его допустимые названия.
    """

    code: MetricCode
    name_ru: str
    aliases: tuple[str, ...]


METRIC_CATALOG: tuple[MetricDefinition, ...] = (
    MetricDefinition(
        code=MetricCode.REVENUE,
        name_ru="Выручка",
        aliases=(
            "revenue",
            "revenues",
            "sales",
            "выручка",
        ),
    ),
    MetricDefinition(
        code=MetricCode.EBITDA,
        name_ru="EBITDA",
        aliases=(
            "ebitda",
            "ебитда",
        ),
    ),
    MetricDefinition(
        code=MetricCode.ADJUSTED_EBITDA,
        name_ru="Скорректированная EBITDA",
        aliases=(
            "adjusted ebitda",
            "скорректированная ebitda",
            "скорректированная ебитда",
        ),
    ),
    MetricDefinition(
        code=MetricCode.OPERATING_PROFIT,
        name_ru="Операционная прибыль",
        aliases=(
            "operating profit",
            "operating income",
            "операционная прибыль",
            "прибыль от операционной деятельности",
        ),
    ),
    MetricDefinition(
        code=MetricCode.NET_INCOME,
        name_ru="Чистая прибыль",
        aliases=(
            "net income",
            "net profit",
            "чистая прибыль",
        ),
    ),
    MetricDefinition(
        code=MetricCode.TOTAL_ASSETS,
        name_ru="Активы",
        aliases=(
            "total assets",
            "assets",
            "активы",
            "всего активов",
        ),
    ),
    MetricDefinition(
        code=MetricCode.TOTAL_EQUITY,
        name_ru="Капитал",
        aliases=(
            "total equity",
            "equity",
            "капитал",
            "собственный капитал",
        ),
    ),
    MetricDefinition(
        code=MetricCode.TOTAL_DEBT,
        name_ru="Общий долг",
        aliases=(
            "total debt",
            "debt",
            "общий долг",
            "совокупный долг",
        ),
    ),
    MetricDefinition(
        code=MetricCode.CASH_AND_EQUIVALENTS,
        name_ru="Денежные средства и их эквиваленты",
        aliases=(
            "cash and cash equivalents",
            "cash equivalents",
            "денежные средства и их эквиваленты",
            "денежные средства",
        ),
    ),
    MetricDefinition(
        code=MetricCode.NET_DEBT,
        name_ru="Чистый долг",
        aliases=(
            "net debt",
            "чистый долг",
        ),
    ),
    MetricDefinition(
        code=MetricCode.CAPEX,
        name_ru="Капитальные затраты",
        aliases=(
            "capex",
            "capital expenditure",
            "capital expenditures",
            "капитальные затраты",
            "капитальные расходы",
        ),
    ),
    MetricDefinition(
        code=MetricCode.OPERATING_CASH_FLOW,
        name_ru="Операционный денежный поток",
        aliases=(
            "operating cash flow",
            "cash flow from operating activities",
            "операционный денежный поток",
            "денежный поток от операционной деятельности",
        ),
    ),
    MetricDefinition(
        code=MetricCode.FREE_CASH_FLOW,
        name_ru="Свободный денежный поток",
        aliases=(
            "free cash flow",
            "fcf",
            "свободный денежный поток",
        ),
    ),
    MetricDefinition(
        code=MetricCode.INTEREST_EXPENSE,
        name_ru="Процентные расходы",
        aliases=(
            "interest expense",
            "interest expenses",
            "процентные расходы",
        ),
    ),
    MetricDefinition(
        code=MetricCode.DIVIDENDS,
        name_ru="Дивиденды",
        aliases=(
            "dividends",
            "dividend payments",
            "дивиденды",
            "дивидендные выплаты",
        ),
    ),
)


def normalize_metric_text(value: str) -> str:
    """
    Нормализует название показателя перед поиском в каталоге.
    """
    normalized = value.strip().lower()
    normalized = re.sub(r"\s+", " ", normalized)

    return normalized


def resolve_metric(value: str) -> MetricCode | None:
    """
    Преобразует пользовательское название показателя
    в канонический код.
    """
    normalized_value = normalize_metric_text(value)

    for definition in METRIC_CATALOG:
        aliases = {
            normalize_metric_text(alias)
            for alias in definition.aliases
        }

        if normalized_value in aliases:
            return definition.code

    return None