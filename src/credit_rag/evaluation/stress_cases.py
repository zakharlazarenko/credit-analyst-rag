from decimal import Decimal

from credit_rag.assistant.dispatcher import DispatchStatus
from credit_rag.assistant.routing import QuestionIntent
from credit_rag.evaluation.schemas import (
    AssistantGoldenCase,
    ExpectedNumericResult,
)

STRESS_CASES = (
    # -------------------------------------------------
    # FACT — новые формулировки
    # -------------------------------------------------

    AssistantGoldenCase(
        case_id="stress_fact_rosneft_revenue_paraphrase",
        question=(
            "Сколько составила выручка "
            "Роснефти в 2025?"
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
        case_id="stress_fact_tatneft_cash",
        question=(
            "Покажи денежные средства "
            "и их эквиваленты Татнефти "
            "за 2024 год."
        ),
        expected_intent=QuestionIntent.FACT,
        expected_status=DispatchStatus.COMPLETED,
        expected_tool="query_facts",
        expected_companies=("TATNEFT",),
        expected_metric="cash_and_equivalents",
        expected_period="2024",
        expected_from_period=None,
        expected_to_period=None,
        expected_numeric_result=ExpectedNumericResult(
            value=Decimal(117454),
            tolerance=Decimal(0),
        ),
    ),

    # -------------------------------------------------
    # DERIVED METRIC — другая формулировка
    # -------------------------------------------------

    AssistantGoldenCase(
        case_id="stress_derived_lukoil_leverage",
        question=(
            "Чему равно отношение чистого долга "
            "к EBITDA ЛУКОЙЛа в 2025 году?"
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

    # -------------------------------------------------
    # COMPARISON — новые формулировки
    # -------------------------------------------------

    AssistantGoldenCase(
        case_id="stress_comparison_operating_profit",
        question=(
            "Сопоставь операционную прибыль "
            "Роснефти и Татнефти за 2025 год."
        ),
        expected_intent=QuestionIntent.COMPARISON,
        expected_status=DispatchStatus.COMPLETED,
        expected_tool="compare_companies",
        expected_companies=(
            "ROSNEFT",
            "TATNEFT",
        ),
        expected_metric="operating_profit",
        expected_period="2025",
        expected_from_period=None,
        expected_to_period=None,
    ),

    # -------------------------------------------------
    # GROWTH — синонимы / implicit periods
    # -------------------------------------------------

    AssistantGoldenCase(
        case_id="stress_growth_tatneft_ocf_yoy",
        question=(
            "Что произошло с операционным "
            "денежным потоком Татнефти "
            "год к году?"
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
        case_id="stress_growth_rosneft_operating_profit",
        question=(
            "На сколько изменилась операционная "
            "прибыль Роснефти между 2024 "
            "и 2025 годами?"
        ),
        expected_intent=QuestionIntent.GROWTH,
        expected_status=DispatchStatus.COMPLETED,
        expected_tool="calculate_growth",
        expected_companies=("ROSNEFT",),
        expected_metric="operating_profit",
        expected_period=None,
        expected_from_period="2024",
        expected_to_period="2025",
        expected_numeric_result=ExpectedNumericResult(
            value=Decimal(
                "-48.94316580554250821982151245"
            ),
            tolerance=Decimal("0.000001"),
        ),
    ),

    # -------------------------------------------------
    # GUARDRAIL — temporal comparability
    # -------------------------------------------------

    AssistantGoldenCase(
        case_id="stress_lukoil_revenue_growth_blocked",
        question=(
            "Как изменилась выручка ЛУКОЙЛа "
            "с 2024 по 2025 год?"
        ),
        expected_intent=QuestionIntent.GROWTH,
        expected_status=DispatchStatus.ERROR,
        expected_tool=None,
        expected_companies=("LUKOIL",),
        expected_metric="revenue",
        expected_period=None,
        expected_from_period="2024",
        expected_to_period="2025",
        notes=(
            "Расчет должен быть заблокирован "
            "из-за temporal comparability."
        ),
    ),

    # -------------------------------------------------
    # MISSING ARGUMENT
    # -------------------------------------------------

    AssistantGoldenCase(
        case_id="stress_fact_missing_period",
        question=(
            "Какая выручка Роснефти?"
        ),
        expected_intent=QuestionIntent.FACT,
        expected_status=(
            DispatchStatus.NEEDS_CLARIFICATION
        ),
        expected_tool=None,
        expected_companies=("ROSNEFT",),
        expected_metric="revenue",
        expected_period=None,
        expected_from_period=None,
        expected_to_period=None,
    ),

    # -------------------------------------------------
    # QUALITATIVE — другая компания
    # -------------------------------------------------

    AssistantGoldenCase(
        case_id="stress_qualitative_rosneft_2024",
        question=(
            "Какие риски отмечает Роснефть "
            "в годовом отчете за 2024 год?"
        ),
        expected_intent=QuestionIntent.QUALITATIVE,
        expected_status=DispatchStatus.COMPLETED,
        expected_tool="retrieve_docs",
        expected_companies=("ROSNEFT",),
        expected_metric=None,
        expected_period="2024",
        expected_from_period=None,
        expected_to_period=None,
    ),

    # -------------------------------------------------
    # UNSUPPORTED
    # -------------------------------------------------

    AssistantGoldenCase(
        case_id="stress_definition_ebitda",
        question="Объясни простыми словами, что такое EBITDA.",
        expected_intent=QuestionIntent.UNKNOWN,
        expected_status=DispatchStatus.UNSUPPORTED,
        expected_tool=None,
        expected_companies=(),
        expected_metric=None,
        expected_period=None,
        expected_from_period=None,
        expected_to_period=None,
    ),
)