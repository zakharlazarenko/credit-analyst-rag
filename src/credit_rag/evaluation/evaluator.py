from dataclasses import dataclass
from decimal import Decimal

from credit_rag.assistant.dispatcher import DispatchResult
from credit_rag.evaluation.schemas import AssistantGoldenCase


@dataclass(frozen=True)
class CaseEvaluationResult:
    """
    Результат проверки одного golden case.
    """

    case_id: str

    intent_correct: bool
    status_correct: bool
    tool_correct: bool
    companies_correct: bool
    metric_correct: bool
    period_correct: bool
    from_period_correct: bool
    to_period_correct: bool

    numeric_checked: bool
    numeric_correct: bool

    errors: tuple[str, ...]

    @property
    def arguments_correct(self) -> bool:
        """
        Совокупная корректность аргументов.
        """
        return all(
            (
                self.companies_correct,
                self.metric_correct,
                self.period_correct,
                self.from_period_correct,
                self.to_period_correct,
            )
        )

    @property
    def passed(self) -> bool:
        """
        Golden case считается полностью пройденным,
        если корректны routing, аргументы и,
        при необходимости, числовой результат.
        """
        base_checks = all(
            (
                self.intent_correct,
                self.status_correct,
                self.tool_correct,
                self.arguments_correct,
            )
        )

        if not base_checks:
            return False

        if self.numeric_checked:
            return self.numeric_correct

        return True


def extract_numeric_result(
    result: DispatchResult,
) -> Decimal | None:
    """
    Извлекает основной детерминированный
    числовой результат из payload.

    Поддерживаемые tools:
    - query_facts
    - compute_metric
    - calculate_growth
    """

    payload = result.payload

    if payload is None:
        return None

    tool_name = result.tool_name

    if tool_name == "query_facts":
        facts = payload.get(
            "facts",
            [],
        )

        if len(facts) != 1:
            return None

        return Decimal(
            str(facts[0]["value"])
        )

    if tool_name == "compute_metric":
        return Decimal(
            str(payload["value"])
        )

    if tool_name == "calculate_growth":
        return Decimal(
            str(payload["growth_pct"])
        )

    return None


def evaluate_numeric_result(
    case: AssistantGoldenCase,
    result: DispatchResult,
) -> tuple[bool, bool, str | None]:
    """
    Проверяет числовой результат
    с заданным tolerance.

    Возвращает:
    numeric_checked,
    numeric_correct,
    error_message.
    """

    expected = (
        case.expected_numeric_result
    )

    if expected is None:
        return (
            False,
            True,
            None,
        )

    actual = extract_numeric_result(
        result
    )

    if actual is None:
        return (
            True,
            False,
            (
                "Не удалось извлечь "
                "числовой результат."
            ),
        )

    difference = abs(
        actual - expected.value
    )

    is_correct = (
        difference
        <= expected.tolerance
    )

    if is_correct:
        return (
            True,
            True,
            None,
        )

    return (
        True,
        False,
        (
            "Числовой результат отличается: "
            f"expected={expected.value}, "
            f"actual={actual}, "
            f"difference={difference}, "
            f"tolerance={expected.tolerance}"
        ),
    )


def evaluate_case(
    case: AssistantGoldenCase,
    result: DispatchResult,
) -> CaseEvaluationResult:
    """
    Сравнивает один реальный DispatchResult
    с ручным golden case.
    """

    parsed = result.parsed_question

    intent_correct = (
        parsed.intent
        == case.expected_intent
    )

    status_correct = (
        result.status
        == case.expected_status
    )

    tool_correct = (
        result.tool_name
        == case.expected_tool
    )

    companies_correct = (
        parsed.company_ids
        == case.expected_companies
    )

    metric_correct = (
        parsed.metric
        == case.expected_metric
    )

    period_correct = (
        parsed.period
        == case.expected_period
    )

    from_period_correct = (
        parsed.from_period
        == case.expected_from_period
    )

    to_period_correct = (
        parsed.to_period
        == case.expected_to_period
    )

    (
        numeric_checked,
        numeric_correct,
        numeric_error,
    ) = evaluate_numeric_result(
        case=case,
        result=result,
    )

    errors: list[str] = []

    if not intent_correct:
        errors.append(
            "Intent mismatch: "
            f"expected={case.expected_intent.value}, "
            f"actual={parsed.intent.value}"
        )

    if not status_correct:
        errors.append(
            "Status mismatch: "
            f"expected={case.expected_status.value}, "
            f"actual={result.status.value}"
        )

    if not tool_correct:
        errors.append(
            "Tool mismatch: "
            f"expected={case.expected_tool}, "
            f"actual={result.tool_name}"
        )

    if not companies_correct:
        errors.append(
            "Companies mismatch: "
            f"expected={case.expected_companies}, "
            f"actual={parsed.company_ids}"
        )

    if not metric_correct:
        errors.append(
            "Metric mismatch: "
            f"expected={case.expected_metric}, "
            f"actual={parsed.metric}"
        )

    if not period_correct:
        errors.append(
            "Period mismatch: "
            f"expected={case.expected_period}, "
            f"actual={parsed.period}"
        )

    if not from_period_correct:
        errors.append(
            "from_period mismatch: "
            f"expected={case.expected_from_period}, "
            f"actual={parsed.from_period}"
        )

    if not to_period_correct:
        errors.append(
            "to_period mismatch: "
            f"expected={case.expected_to_period}, "
            f"actual={parsed.to_period}"
        )

    if numeric_error is not None:
        errors.append(
            numeric_error
        )

    return CaseEvaluationResult(
        case_id=case.case_id,
        intent_correct=intent_correct,
        status_correct=status_correct,
        tool_correct=tool_correct,
        companies_correct=companies_correct,
        metric_correct=metric_correct,
        period_correct=period_correct,
        from_period_correct=from_period_correct,
        to_period_correct=to_period_correct,
        numeric_checked=numeric_checked,
        numeric_correct=numeric_correct,
        errors=tuple(errors),
    )


@dataclass(frozen=True)
class EvaluationSummary:
    """
    Итоговые метрики end-to-end evaluation.
    """

    total_cases: int

    passed_cases: int

    intent_correct: int
    status_correct: int
    tool_correct: int
    arguments_correct: int

    numeric_total: int
    numeric_correct: int

    @property
    def overall_accuracy(self) -> float:
        if self.total_cases == 0:
            return 0.0

        return (
            self.passed_cases
            / self.total_cases
        )

    @property
    def intent_accuracy(self) -> float:
        if self.total_cases == 0:
            return 0.0

        return (
            self.intent_correct
            / self.total_cases
        )

    @property
    def tool_accuracy(self) -> float:
        if self.total_cases == 0:
            return 0.0

        return (
            self.tool_correct
            / self.total_cases
        )

    @property
    def argument_accuracy(self) -> float:
        if self.total_cases == 0:
            return 0.0

        return (
            self.arguments_correct
            / self.total_cases
        )

    @property
    def numeric_accuracy(self) -> float:
        if self.numeric_total == 0:
            return 0.0

        return (
            self.numeric_correct
            / self.numeric_total
        )


def build_summary(
    results: tuple[
        CaseEvaluationResult,
        ...
    ],
) -> EvaluationSummary:
    """
    Собирает агрегированные метрики.
    """

    numeric_results = [
        result
        for result in results
        if result.numeric_checked
    ]

    return EvaluationSummary(
        total_cases=len(results),

        passed_cases=sum(
            result.passed
            for result in results
        ),

        intent_correct=sum(
            result.intent_correct
            for result in results
        ),

        status_correct=sum(
            result.status_correct
            for result in results
        ),

        tool_correct=sum(
            result.tool_correct
            for result in results
        ),

        arguments_correct=sum(
            result.arguments_correct
            for result in results
        ),

        numeric_total=len(
            numeric_results
        ),

        numeric_correct=sum(
            result.numeric_correct
            for result in numeric_results
        ),
    )