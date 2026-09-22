from dataclasses import dataclass
from decimal import Decimal

from credit_rag.assistant.dispatcher import DispatchStatus
from credit_rag.assistant.routing import QuestionIntent


@dataclass(frozen=True)
class ExpectedNumericResult:
    """
    Ожидаемый числовой результат.

    Используется только для вопросов,
    где существует детерминированное число.
    """

    value: Decimal
    tolerance: Decimal


@dataclass(frozen=True)
class AssistantGoldenCase:
    """
    Один end-to-end golden test
    помощника кредитного аналитика.
    """

    case_id: str

    question: str

    expected_intent: QuestionIntent

    expected_status: DispatchStatus

    expected_tool: str | None

    expected_companies: tuple[str, ...]

    expected_metric: str | None

    expected_period: str | None

    expected_from_period: str | None
    expected_to_period: str | None

    expected_numeric_result: (
        ExpectedNumericResult | None
    ) = None

    notes: str = ""