from decimal import Decimal

from credit_rag.assistant.dispatcher import DispatchStatus
from credit_rag.assistant.routing import QuestionIntent
from credit_rag.evaluation.schemas import (
    AssistantGoldenCase,
    ExpectedNumericResult,
)

GOLDEN_CASES = (
    AssistantGoldenCase(
        case_id="fact_revenue_rosneft_2025",
        question=(
            "Какая выручка Роснефти "
            "за 2025 год?"
        ),
        expected_intent=QuestionIntent.FACT,
        expected_status=DispatchStatus.COMPLETED,
        expected_tool="query_facts",
        expected_companies=("ROSNEFT",),
        expected_metric="revenue",
        expected_period="2025",
        expected_from_period=None,
        expected_to_period=None,
        expected_numeric_result=ExpectedNumericResult(
            value=Decimal(8236),
            tolerance=Decimal(0),
        ),
    ),

    AssistantGoldenCase(
        case_id="derived_lukoil_leverage_2025",
        question=(
            "Какой Net Debt / EBITDA "
            "у ЛУКОЙЛа за 2025 год?"
        ),
        expected_intent=(
            QuestionIntent.DERIVED_METRIC
        ),
        expected_status=DispatchStatus.COMPLETED,
        expected_tool="compute_metric",
        expected_companies=("LUKOIL",),
        expected_metric="net_debt_to_ebitda",
        expected_period="2025",
        expected_from_period=None,
        expected_to_period=None,
        expected_numeric_result=ExpectedNumericResult(
            value=Decimal(
                "-0.2531179729308609259645370514"
            ),
            tolerance=Decimal("0.000001"),
        ),
    ),

    AssistantGoldenCase(
        case_id="comparison_revenue_2025",
        question=(
            "Сравни выручку ЛУКОЙЛа, "
            "Роснефти и Татнефти "
            "за 2025 год."
        ),
        expected_intent=QuestionIntent.COMPARISON,
        expected_status=DispatchStatus.COMPLETED,
        expected_tool="compare_companies",
        expected_companies=(
            "LUKOIL",
            "ROSNEFT",
            "TATNEFT",
        ),
        expected_metric="revenue",
        expected_period="2025",
        expected_from_period=None,
        expected_to_period=None,
    ),

    AssistantGoldenCase(
        case_id="growth_rosneft_revenue",
        question=(
            "Как изменилась выручка Роснефти "
            "с 2024 по 2025 год?"
        ),
        expected_intent=QuestionIntent.GROWTH,
        expected_status=DispatchStatus.COMPLETED,
        expected_tool="calculate_growth",
        expected_companies=("ROSNEFT",),
        expected_metric="revenue",
        expected_period=None,
        expected_from_period="2024",
        expected_to_period="2025",
        expected_numeric_result=ExpectedNumericResult(
            value=Decimal(
                "-18.76910937962323700562185620"
            ),
            tolerance=Decimal("0.000001"),
        ),
    ),

    AssistantGoldenCase(
        case_id="growth_tatneft_ocf_auto_period",
        question=(
            "На сколько процентов снизился "
            "операционный денежный поток "
            "Татнефти?"
        ),
        expected_intent=QuestionIntent.GROWTH,
        expected_status=DispatchStatus.COMPLETED,
        expected_tool="calculate_growth",
        expected_companies=("TATNEFT",),
        expected_metric="operating_cash_flow",
        expected_period=None,
        expected_from_period="2024",
        expected_to_period="2025",
        expected_numeric_result=ExpectedNumericResult(
            value=Decimal(
                "-38.41986785187554836296747575"
            ),
            tolerance=Decimal("0.000001"),
        ),
    ),

    AssistantGoldenCase(
        case_id="qualitative_lukoil_risks_2025",
        question=(
            "Какие основные риски описывает "
            "ЛУКОЙЛ в годовом отчете "
            "за 2025 год?"
        ),
        expected_intent=QuestionIntent.QUALITATIVE,
        expected_status=DispatchStatus.COMPLETED,
        expected_tool="retrieve_docs",
        expected_companies=("LUKOIL",),
        expected_metric=None,
        expected_period="2025",
        expected_from_period=None,
        expected_to_period=None,
    ),

    AssistantGoldenCase(
        case_id="qualitative_missing_period",
        question=(
            "Какие основные риски "
            "описывает ЛУКОЙЛ?"
        ),
        expected_intent=QuestionIntent.QUALITATIVE,
        expected_status=(
            DispatchStatus.NEEDS_CLARIFICATION
        ),
        expected_tool=None,
        expected_companies=("LUKOIL",),
        expected_metric=None,
        expected_period=None,
        expected_from_period=None,
        expected_to_period=None,
    ),

    AssistantGoldenCase(
        case_id="unsupported_credit_decision",
        question=(
            "Стоит ли выдавать ЛУКОЙЛу кредит?"
        ),
        expected_intent=QuestionIntent.UNKNOWN,
        expected_status=DispatchStatus.UNSUPPORTED,
        expected_tool=None,
        expected_companies=("LUKOIL",),
        expected_metric=None,
        expected_period=None,
        expected_from_period=None,
        expected_to_period=None,
    ),
)