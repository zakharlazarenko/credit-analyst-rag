import pytest

from credit_rag.assistant.routing import (
    ParsedQuestion,
    QuestionIntent,
)
from credit_rag.assistant.validation import (
    validate_parsed_question,
)


@pytest.mark.parametrize(
    ("parsed", "expected_status"),
    [
        (
            ParsedQuestion(
                intent=QuestionIntent.FACT,
                company_ids=("ROSNEFT",),
                metric="revenue",
                period="2025",
                from_period=None,
                to_period=None,
                reason="Test.",
            ),
            "valid",
        ),
        (
            ParsedQuestion(
                intent=QuestionIntent.DERIVED_METRIC,
                company_ids=("LUKOIL",),
                metric="net_debt_to_ebitda",
                period="2025",
                from_period=None,
                to_period=None,
                reason="Test.",
            ),
            "valid",
        ),
        (
            ParsedQuestion(
                intent=QuestionIntent.COMPARISON,
                company_ids=(
                    "LUKOIL",
                    "ROSNEFT",
                    "TATNEFT",
                ),
                metric="revenue",
                period="2025",
                from_period=None,
                to_period=None,
                reason="Test.",
            ),
            "valid",
        ),
        (
            ParsedQuestion(
                intent=QuestionIntent.GROWTH,
                company_ids=("ROSNEFT",),
                metric="revenue",
                period=None,
                from_period="2024",
                to_period="2025",
                reason="Test.",
            ),
            "valid",
        ),
        (
            ParsedQuestion(
                intent=QuestionIntent.QUALITATIVE,
                company_ids=("LUKOIL",),
                metric=None,
                period=None,
                from_period=None,
                to_period=None,
                reason="Test.",
            ),
            "incomplete",
        ),
        (
            ParsedQuestion(
                intent=QuestionIntent.UNKNOWN,
                company_ids=("LUKOIL",),
                metric=None,
                period=None,
                from_period=None,
                to_period=None,
                reason="Test.",
            ),
            "valid",
        ),
    ],
)
def test_validate_parsed_question(
    parsed: ParsedQuestion,
    expected_status: str,
) -> None:
    result = validate_parsed_question(
        parsed
    )

    assert result.status.value == expected_status