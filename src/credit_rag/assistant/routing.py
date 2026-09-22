from dataclasses import dataclass
from enum import StrEnum


class QuestionIntent(StrEnum):
    """
    Тип задачи, которую должен выполнить
    помощник кредитного аналитика.
    """

    QUALITATIVE = "qualitative"
    FACT = "fact"
    DERIVED_METRIC = "derived_metric"
    COMPARISON = "comparison"
    GROWTH = "growth"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class QuestionRoute:
    """
    Результат базовой маршрутизации вопроса.

    Используется, когда нужно определить
    только intent без извлечения аргументов.
    """

    intent: QuestionIntent
    reason: str


@dataclass(frozen=True)
class ParsedQuestion:
    """
    Структурированное представление
    пользовательского вопроса.

    Содержит не только intent,
    но и извлеченные аргументы,
    необходимые для вызова инструментов.
    """

    intent: QuestionIntent

    # Одна или несколько компаний.
    # Например:
    # ("LUKOIL",)
    # ("LUKOIL", "ROSNEFT", "TATNEFT")
    company_ids: tuple[str, ...]

    # Каноническое имя финансовой метрики.
    #
    # Например:
    # "revenue"
    # "ebitda"
    # "net_debt_to_ebitda"
    #
    # Пока оставляем str, потому что обычные
    # и расчетные метрики принадлежат
    # разным enum.
    metric: str | None

    # Один конкретный период.
    #
    # Используется, например, для:
    # FACT
    # COMPARISON
    #
    # Пример:
    # "2025"
    period: str | None

    # Начальный и конечный периоды.
    #
    # Используются прежде всего
    # для GROWTH.
    #
    # Пример:
    # from_period = "2024"
    # to_period = "2025"
    from_period: str | None
    to_period: str | None

    # Короткое объяснение решения router/parser.
    reason: str