import pytest

from credit_rag.assistant.routing import (
    QuestionIntent,
    QuestionRoute,
)


@pytest.mark.parametrize(
    "intent",
    [
        QuestionIntent.QUALITATIVE,
        QuestionIntent.FACT,
        QuestionIntent.DERIVED_METRIC,
        QuestionIntent.COMPARISON,
        QuestionIntent.GROWTH,
        QuestionIntent.UNKNOWN,
    ],
)
def test_question_route_supports_intents(
    intent: QuestionIntent,
) -> None:
    route = QuestionRoute(
        intent=intent,
        reason="Test reason.",
    )

    assert route.intent == intent
    assert route.reason == "Test reason."