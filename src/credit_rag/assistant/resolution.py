from collections.abc import Sequence
from dataclasses import dataclass, replace
from enum import StrEnum

from credit_rag.assistant.routing import (
    ParsedQuestion,
    QuestionIntent,
)
from credit_rag.financial.metrics import MetricCode
from credit_rag.financial.schemas import (
    FinancialFact,
    FinancialStandard,
)
from credit_rag.financial.temporal_comparability import (
    TemporalComparabilityStatus,
    assess_temporal_comparability,
)


class ResolutionStatus(StrEnum):
    """
    Результат автоматического разрешения
    недостающих аргументов.
    """

    NOT_NEEDED = "not_needed"
    RESOLVED = "resolved"
    UNRESOLVED = "unresolved"


@dataclass(frozen=True)
class QuestionResolution:
    """
    Результат resolver-слоя.
    """

    status: ResolutionStatus

    parsed_question: ParsedQuestion

    resolved_fields: tuple[str, ...]
    unresolved_fields: tuple[str, ...]

    message: str


def period_sort_key(
    period: str,
) -> tuple[int, int | str]:
    """
    Ключ сортировки периодов.

    Годовые периоды вроде "2024" и "2025"
    сортируются численно.
    """

    if period.isdigit():
        return (
            0,
            int(period),
        )

    return (
        1,
        period,
    )


def find_available_periods(
    facts: Sequence[FinancialFact],
    company_id: str,
    metric: MetricCode,
    standard: FinancialStandard,
) -> tuple[str, ...]:
    """
    Возвращает периоды, для которых
    в fact store существует нужная метрика.
    """

    periods = {
        fact.period
        for fact in facts
        if (
            fact.company_id == company_id
            and fact.metric == metric
            and fact.standard == standard
        )
    }

    return tuple(
        sorted(
            periods,
            key=period_sort_key,
        )
    )


def find_comparable_period_pairs(
    company_id: str,
    metric: MetricCode,
    periods: Sequence[str],
) -> tuple[tuple[str, str], ...]:
    """
    Находит пары периодов, для которых
    temporal comparability подтверждена.
    """

    pairs: list[tuple[str, str]] = []

    for index, from_period in enumerate(
        periods
    ):
        for to_period in periods[
            index + 1:
        ]:
            comparability = (
                assess_temporal_comparability(
                    company_id=company_id,
                    metric=metric,
                    from_period=from_period,
                    to_period=to_period,
                )
            )

            if (
                comparability.status
                == TemporalComparabilityStatus.COMPARABLE
            ):
                pairs.append(
                    (
                        from_period,
                        to_period,
                    )
                )

    return tuple(
        pairs
    )


def resolve_growth_periods(
    parsed: ParsedQuestion,
    facts: Sequence[FinancialFact],
    standard: FinancialStandard = FinancialStandard.IFRS,
) -> QuestionResolution:
    """
    Автоматически определяет периоды для growth,
    только если существует ровно одна
    однозначная сопоставимая пара.
    """

    if parsed.intent != QuestionIntent.GROWTH:
        return QuestionResolution(
            status=ResolutionStatus.NOT_NEEDED,
            parsed_question=parsed,
            resolved_fields=(),
            unresolved_fields=(),
            message=(
                "Resolver периодов нужен "
                "только для growth."
            ),
        )

    if (
        parsed.from_period is not None
        and parsed.to_period is not None
    ):
        return QuestionResolution(
            status=ResolutionStatus.NOT_NEEDED,
            parsed_question=parsed,
            resolved_fields=(),
            unresolved_fields=(),
            message=(
                "Оба периода уже указаны."
            ),
        )

    missing_fields = []

    if parsed.from_period is None:
        missing_fields.append(
            "from_period"
        )

    if parsed.to_period is None:
        missing_fields.append(
            "to_period"
        )

    if len(parsed.company_ids) != 1:
        return QuestionResolution(
            status=ResolutionStatus.UNRESOLVED,
            parsed_question=parsed,
            resolved_fields=(),
            unresolved_fields=tuple(
                missing_fields
            ),
            message=(
                "Нельзя определить периоды: "
                "для growth требуется одна компания."
            ),
        )

    if parsed.metric is None:
        return QuestionResolution(
            status=ResolutionStatus.UNRESOLVED,
            parsed_question=parsed,
            resolved_fields=(),
            unresolved_fields=tuple(
                missing_fields
            ),
            message=(
                "Нельзя определить периоды: "
                "не указана метрика."
            ),
        )

    try:
        metric = MetricCode(
            parsed.metric
        )

    except ValueError:
        return QuestionResolution(
            status=ResolutionStatus.UNRESOLVED,
            parsed_question=parsed,
            resolved_fields=(),
            unresolved_fields=tuple(
                missing_fields
            ),
            message=(
                "Нельзя определить периоды: "
                "метрика не является обычной "
                "финансовой метрикой."
            ),
        )

    company_id = parsed.company_ids[0]

    available_periods = (
        find_available_periods(
            facts=facts,
            company_id=company_id,
            metric=metric,
            standard=standard,
        )
    )

    comparable_pairs = list(
        find_comparable_period_pairs(
            company_id=company_id,
            metric=metric,
            periods=available_periods,
        )
    )

    # Если пользователь уже указал один
    # из периодов, оставляем только пары,
    # совместимые с этим значением.

    if parsed.from_period is not None:
        comparable_pairs = [
            pair
            for pair in comparable_pairs
            if pair[0] == parsed.from_period
        ]

    if parsed.to_period is not None:
        comparable_pairs = [
            pair
            for pair in comparable_pairs
            if pair[1] == parsed.to_period
        ]

    # Автоматическое разрешение допустимо
    # только при одной однозначной паре.

    if len(comparable_pairs) != 1:
        return QuestionResolution(
            status=ResolutionStatus.UNRESOLVED,
            parsed_question=parsed,
            resolved_fields=(),
            unresolved_fields=tuple(
                missing_fields
            ),
            message=(
                "Не удалось однозначно определить "
                "подтвержденную сопоставимую пару периодов. "
                f"Доступные периоды: {available_periods}. "
                f"Подходящие пары: {tuple(comparable_pairs)}."
            ),
        )

    resolved_from_period, resolved_to_period = (
        comparable_pairs[0]
    )

    resolved_fields = []

    if parsed.from_period is None:
        resolved_fields.append(
            "from_period"
        )

    if parsed.to_period is None:
        resolved_fields.append(
            "to_period"
        )

    resolved_question = replace(
        parsed,
        from_period=(
            parsed.from_period
            or resolved_from_period
        ),
        to_period=(
            parsed.to_period
            or resolved_to_period
        ),
    )

    return QuestionResolution(
        status=ResolutionStatus.RESOLVED,
        parsed_question=resolved_question,
        resolved_fields=tuple(
            resolved_fields
        ),
        unresolved_fields=(),
        message=(
            "Недостающие периоды определены "
            "по FinancialFact Store и проверке "
            "temporal comparability."
        ),
    )