from decimal import Decimal
from enum import StrEnum


class UnitCode(StrEnum):
    """
    Канонические единицы измерения финансовых показателей.
    """

    RUB = "RUB"
    RUB_THOUSAND = "RUB_THOUSAND"
    RUB_MILLION = "RUB_MILLION"
    RUB_BILLION = "RUB_BILLION"


RUB_MULTIPLIERS = {
    UnitCode.RUB: Decimal(1),
    UnitCode.RUB_THOUSAND: Decimal(1000),
    UnitCode.RUB_MILLION: Decimal(1000000),
    UnitCode.RUB_BILLION: Decimal(1000000000),
}


def convert_monetary_value(
    value: Decimal,
    source_unit: UnitCode,
    target_unit: UnitCode,
) -> Decimal:
    """
    Конвертирует денежное значение между единицами рублей.
    """
    value_in_rubles = (
        value
        * RUB_MULTIPLIERS[source_unit]
    )

    return (
        value_in_rubles
        / RUB_MULTIPLIERS[target_unit]
    )