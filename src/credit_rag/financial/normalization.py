from credit_rag.financial.schemas import FinancialFact
from credit_rag.financial.units import (
    UnitCode,
    convert_monetary_value,
)


def normalize_fact_unit(
    fact: FinancialFact,
    target_unit: UnitCode,
) -> FinancialFact:
    """
    Создает копию финансового факта,
    приведенную к заданной денежной единице.
    """
    normalized_value = convert_monetary_value(
        value=fact.value,
        source_unit=fact.unit,
        target_unit=target_unit,
    )

    return fact.model_copy(
        update={
            "value": normalized_value,
            "unit": target_unit,
        }
    )