from dataclasses import dataclass
from enum import StrEnum

from credit_rag.assistant.routing import (
    ParsedQuestion,
    QuestionIntent,
)
from credit_rag.financial.calculations import DerivedMetricCode
from credit_rag.financial.metrics import MetricCode

SUPPORTED_COMPANIES = {
    "LUKOIL",
    "ROSNEFT",
    "TATNEFT",
}


class ParsedQuestionStatus(StrEnum):
    """
    Результат проверки ParsedQuestion.
    """

    VALID = "valid"
    INCOMPLETE = "incomplete"
    INVALID = "invalid"


@dataclass(frozen=True)
class ParsedQuestionValidation:
    """
    Результат детерминированной проверки
    структурированного вопроса.
    """

    status: ParsedQuestionStatus
    errors: tuple[str, ...]
    missing_fields: tuple[str, ...]

    @property
    def is_valid(self) -> bool:
        return self.status == ParsedQuestionStatus.VALID


def is_regular_metric(
    metric: str | None,
) -> bool:
    """
    Проверяет, является ли строка
    обычной MetricCode.
    """
    if metric is None:
        return False

    try:
        MetricCode(metric)
        return True

    except ValueError:
        return False


def is_derived_metric(
    metric: str | None,
) -> bool:
    """
    Проверяет, является ли строка
    расчетной DerivedMetricCode.
    """
    if metric is None:
        return False

    try:
        DerivedMetricCode(metric)
        return True

    except ValueError:
        return False


def validate_companies(
    parsed: ParsedQuestion,
) -> list[str]:
    """
    Проверяет, что LLM не придумала
    неизвестную компанию.
    """
    errors = []

    for company_id in parsed.company_ids:
        if company_id not in SUPPORTED_COMPANIES:
            errors.append(
                f"Неизвестная компания: {company_id}"
            )

    return errors


def validate_parsed_question(
    parsed: ParsedQuestion,
) -> ParsedQuestionValidation:
    """
    Проверяет ParsedQuestion перед вызовом tools.

    INVALID:
    аргументы противоречат контракту.

    INCOMPLETE:
    запрос корректно понят, но пользователь
    не указал необходимые параметры.

    VALID:
    запрос готов к выполнению.
    """

    errors: list[str] = []
    missing_fields: list[str] = []

    errors.extend(
        validate_companies(parsed)
    )

    if parsed.intent == QuestionIntent.FACT:
        if len(parsed.company_ids) == 0:
            missing_fields.append(
                "company_id"
            )

        elif len(parsed.company_ids) > 1:
            errors.append(
                "Для fact должна быть указана одна компания."
            )

        if parsed.metric is None:
            missing_fields.append(
                "metric"
            )

        elif not is_regular_metric(
            parsed.metric
        ):
            errors.append(
                "Для fact требуется обычная "
                "финансовая метрика."
            )

        if parsed.period is None:
            missing_fields.append(
                "period"
            )

    elif (
        parsed.intent
        == QuestionIntent.DERIVED_METRIC
    ):
        if len(parsed.company_ids) == 0:
            missing_fields.append(
                "company_id"
            )

        elif len(parsed.company_ids) > 1:
            errors.append(
                "Для derived_metric должна быть "
                "указана одна компания."
            )

        if parsed.metric is None:
            missing_fields.append(
                "metric"
            )

        elif not is_derived_metric(
            parsed.metric
        ):
            errors.append(
                "Для derived_metric требуется "
                "расчетная финансовая метрика."
            )

        if parsed.period is None:
            missing_fields.append(
                "period"
            )

    elif (
        parsed.intent
        == QuestionIntent.COMPARISON
    ):
        if len(parsed.company_ids) < 2:
            missing_fields.append(
                "companies"
            )

        if parsed.metric is None:
            missing_fields.append(
                "metric"
            )

        elif not is_regular_metric(
            parsed.metric
        ):
            errors.append(
                "Для comparison требуется обычная "
                "финансовая метрика."
            )

        if parsed.period is None:
            missing_fields.append(
                "period"
            )

    elif parsed.intent == QuestionIntent.GROWTH:
        if len(parsed.company_ids) == 0:
            missing_fields.append(
                "company_id"
            )

        elif len(parsed.company_ids) > 1:
            errors.append(
                "Для growth должна быть указана "
                "одна компания."
            )

        if parsed.metric is None:
            missing_fields.append(
                "metric"
            )

        elif not is_regular_metric(
            parsed.metric
        ):
            errors.append(
                "Для growth требуется обычная "
                "финансовая метрика."
            )

        if parsed.from_period is None:
            missing_fields.append(
                "from_period"
            )

        if parsed.to_period is None:
            missing_fields.append(
                "to_period"
            )


    elif (
            parsed.intent
            == QuestionIntent.QUALITATIVE
    ):

        if len(parsed.company_ids) == 0:

            missing_fields.append(
                "company_id"
            )

        elif len(parsed.company_ids) > 1:

            errors.append(
                "Для qualitative-запроса пока "
                "поддерживается одна компания."
            )

        if parsed.period is None:
            missing_fields.append(
                "period"
            )

    elif parsed.intent == QuestionIntent.UNKNOWN:
        # UNKNOWN не передается финансовым tools,
        # поэтому дополнительных обязательных
        # параметров здесь нет.
        pass

    if errors:
        return ParsedQuestionValidation(
            status=ParsedQuestionStatus.INVALID,
            errors=tuple(errors),
            missing_fields=tuple(missing_fields),
        )

    if missing_fields:
        return ParsedQuestionValidation(
            status=ParsedQuestionStatus.INCOMPLETE,
            errors=(),
            missing_fields=tuple(missing_fields),
        )

    return ParsedQuestionValidation(
        status=ParsedQuestionStatus.VALID,
        errors=(),
        missing_fields=(),
    )