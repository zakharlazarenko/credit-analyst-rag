from dataclasses import dataclass
from decimal import Decimal
from enum import StrEnum

from credit_rag.financial.fact_store import query_facts
from credit_rag.financial.metrics import MetricCode
from credit_rag.financial.schemas import (
    FinancialFact,
    FinancialStandard,
)


class ValidationStatus(StrEnum):
    """
    Статус проверки финансовых данных.
    """

    PASS = "pass"
    FAIL = "fail"
    SKIPPED = "skipped"


@dataclass(frozen=True)
class ValidationResult:
    """
    Представляет результат одной проверки финансовых данных.
    """

    check_name: str
    status: ValidationStatus
    difference: Decimal | None
    tolerance: Decimal | None
    message: str
    source_facts: tuple[FinancialFact, ...]


def validate_net_debt_identity(
    facts: list[FinancialFact],
    company_id: str,
    period: str,
    standard: FinancialStandard,
    tolerance: Decimal = Decimal(1),
) -> ValidationResult:
    """
    Проверяет соотношение:

    Net Debt = Total Debt - Cash and Cash Equivalents.
    """
    total_debt_results = query_facts(
        facts=facts,
        company_id=company_id,
        period=period,
        metric=MetricCode.TOTAL_DEBT,
        standard=standard,
    )

    cash_results = query_facts(
        facts=facts,
        company_id=company_id,
        period=period,
        metric=MetricCode.CASH_AND_EQUIVALENTS,
        standard=standard,
    )

    net_debt_results = query_facts(
        facts=facts,
        company_id=company_id,
        period=period,
        metric=MetricCode.NET_DEBT,
        standard=standard,
    )

    result_groups = (
        total_debt_results,
        cash_results,
        net_debt_results,
    )

    if any(len(group) == 0 for group in result_groups):
        return ValidationResult(
            check_name="net_debt_identity",
            status=ValidationStatus.SKIPPED,
            difference=None,
            tolerance=None,
            message="Недостаточно исходных фактов для проверки.",
            source_facts=(),
        )

    if any(len(group) > 1 for group in result_groups):
        return ValidationResult(
            check_name="net_debt_identity",
            status=ValidationStatus.FAIL,
            difference=None,
            tolerance=None,
            message=(
                "Найдено несколько значений одного "
                "из исходных показателей."
            ),
            source_facts=(),
        )

    total_debt = total_debt_results[0]
    cash = cash_results[0]
    net_debt = net_debt_results[0]

    source_facts = (
        total_debt,
        cash,
        net_debt,
    )

    units = {
        total_debt.unit,
        cash.unit,
        net_debt.unit,
    }

    if len(units) != 1:
        return ValidationResult(
            check_name="net_debt_identity",
            status=ValidationStatus.FAIL,
            difference=None,
            tolerance=None,
            message="Единицы измерения показателей различаются.",
            source_facts=source_facts,
        )

    expected_net_debt = (
        total_debt.value
        - cash.value
    )

    difference = abs(
        expected_net_debt
        - net_debt.value
    )

    if difference <= tolerance:
        status = ValidationStatus.PASS
        message = (
            "Чистый долг согласуется с общим долгом "
            "и денежными средствами."
        )
    else:
        status = ValidationStatus.FAIL
        message = (
            "Чистый долг не согласуется с общим долгом "
            "и денежными средствами."
        )

    return ValidationResult(
        check_name="net_debt_identity",
        status=status,
        difference=difference,
        tolerance=tolerance,
        message=message,
        source_facts=source_facts,
    )