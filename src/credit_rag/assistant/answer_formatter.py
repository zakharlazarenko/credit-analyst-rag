from decimal import ROUND_HALF_UP, Decimal

from credit_rag.assistant.dispatcher import (
    DispatchResult,
    DispatchStatus,
)
from credit_rag.assistant.routing import QuestionIntent

COMPANY_NAMES = {
    "LUKOIL": "ЛУКОЙЛ",
    "ROSNEFT": "Роснефть",
    "TATNEFT": "Татнефть",
}


COMPANY_GENITIVE_NAMES = {
    "LUKOIL": "ЛУКОЙЛа",
    "ROSNEFT": "Роснефти",
    "TATNEFT": "Татнефти",
}


METRIC_NAMES = {
    "revenue": "Выручка",
    "ebitda": "EBITDA",
    "adjusted_ebitda": "Скорректированная EBITDA",
    "operating_profit": "Операционная прибыль",
    "net_income": "Чистая прибыль",
    "total_assets": "Активы",
    "total_equity": "Капитал",
    "total_debt": "Общий долг",
    "cash_and_equivalents": (
        "Денежные средства и их эквиваленты"
    ),
    "net_debt": "Чистый долг",
    "capex": "Капитальные затраты",
    "operating_cash_flow": (
        "Операционный денежный поток"
    ),
    "free_cash_flow": (
        "Свободный денежный поток"
    ),
    "interest_expense": "Процентные расходы",
    "dividends": "Дивиденды",

    "net_debt_to_ebitda": "Net Debt / EBITDA",

    "free_cash_flow_calculated": (
        "Рассчитанный свободный денежный поток"
    ),
}


# Нужен только для красивого согласования
# фраз вида "показатель вырос / снизился".
METRIC_GENDERS = {
    "revenue": "feminine",
    "ebitda": "feminine",
    "adjusted_ebitda": "feminine",
    "operating_profit": "feminine",
    "net_income": "feminine",

    "total_assets": "plural",
    "total_equity": "masculine",
    "total_debt": "masculine",
    "cash_and_equivalents": "plural",
    "net_debt": "masculine",
    "capex": "plural",
    "operating_cash_flow": "masculine",
    "free_cash_flow": "masculine",
    "interest_expense": "plural",
    "dividends": "plural",
}


UNIT_NAMES = {
    # Точки специально не ставим.
    # Пунктуацию добавляет предложение.
    "RUB": "руб",
    "RUB_THOUSAND": "тыс. руб",
    "RUB_MILLION": "млн руб",
    "RUB_BILLION": "млрд руб",
    "x": "x",
}


STANDARD_NAMES = {
    "IFRS": "МСФО",
    "RAS": "РСБУ",
}


def format_decimal(
    value: Decimal | str,
    decimal_places: int = 0,
) -> str:
    """
    Форматирует число для пользовательского ответа.

    8236
        -> 8 236

    18.769...
        -> 18,77
    """

    decimal_value = Decimal(
        str(value)
    )

    quantizer = (
        Decimal(1)
        if decimal_places == 0
        else Decimal(1).scaleb(
            -decimal_places
        )
    )

    rounded = decimal_value.quantize(
        quantizer,
        rounding=ROUND_HALF_UP,
    )

    formatted = (
        f"{rounded:,.{decimal_places}f}"
    )

    return (
        formatted
        .replace(",", " ")
        .replace(".", ",")
    )


def format_value(
    value: Decimal | str,
    unit: str,
    decimal_places: int = 0,
) -> str:
    """
    Форматирует число вместе с единицей.
    """

    formatted_value = format_decimal(
        value=value,
        decimal_places=decimal_places,
    )

    unit_name = UNIT_NAMES.get(
        unit,
        unit,
    )

    if unit == "x":
        return (
            f"{formatted_value}{unit_name}"
        )

    return (
        f"{formatted_value} {unit_name}"
    )


def company_name(
    company_id: str,
) -> str:
    """
    Название компании в именительном падеже.
    """

    return COMPANY_NAMES.get(
        company_id,
        company_id,
    )


def company_genitive_name(
    company_id: str,
) -> str:
    """
    Название компании в родительном падеже.
    """

    return COMPANY_GENITIVE_NAMES.get(
        company_id,
        company_id,
    )


def metric_name(
    metric: str,
) -> str:
    """
    Человекочитаемое название метрики.
    """

    return METRIC_NAMES.get(
        metric,
        metric,
    )


def standard_name(
    standard: str,
) -> str:
    """
    Человекочитаемое название
    стандарта отчетности.
    """

    return STANDARD_NAMES.get(
        standard,
        standard,
    )


def format_source(
    source: dict,
) -> str:
    """
    Форматирует provenance FinancialFact.
    """

    company = company_name(
        source["company_id"]
    )

    standard = standard_name(
        source["standard"]
    )

    period = source["period"]
    page = source["page"]

    return (
        f"[{company}, {standard} {period}, "
        f"стр. {page}]"
    )


def growth_direction(
    metric: str,
    growth_pct: Decimal,
) -> str:
    """
    Возвращает глагол с правильным
    грамматическим родом.
    """

    gender = METRIC_GENDERS.get(
        metric,
        "masculine",
    )

    if growth_pct == 0:
        if gender == "feminine":
            return "не изменилась"

        if gender == "plural":
            return "не изменились"

        return "не изменился"

    is_positive = (
        growth_pct > 0
    )

    if gender == "feminine":
        return (
            "выросла"
            if is_positive
            else "снизилась"
        )

    if gender == "plural":
        return (
            "выросли"
            if is_positive
            else "снизились"
        )

    return (
        "вырос"
        if is_positive
        else "снизился"
    )


def format_fact(
    payload: dict,
) -> str:
    """
    Пользовательский ответ для FACT.
    """

    facts = payload["facts"]

    if not facts:
        return (
            "В структурированном хранилище "
            "не найдено значение этого показателя."
        )

    fact = facts[0]

    company = company_genitive_name(
        fact["company_id"]
    )

    metric = metric_name(
        fact["metric"]
    )

    value = format_value(
        value=fact["value"],
        unit=fact["unit"],
    )

    source = format_source(
        fact
    )

    return (
        f"{metric} {company} "
        f"за {fact['period']} год составила "
        f"{value}.\n\n"
        f"Источник: {source}"
    )


def format_derived_metric(
    payload: dict,
) -> str:
    """
    Пользовательский ответ
    для расчетной метрики.
    """

    company = company_genitive_name(
        payload["company_id"]
    )

    metric = metric_name(
        payload["metric"]
    )

    value = format_value(
        value=payload["value"],
        unit=payload["unit"],
        decimal_places=2,
    )

    sources = [
        format_source(source)
        for source
        in payload["source_facts"]
    ]

    unique_sources = list(
        dict.fromkeys(
            sources
        )
    )

    source_text = "\n".join(
        f"- {source}"
        for source in unique_sources
    )

    return (
        f"{metric} {company} "
        f"за {payload['period']} год = "
        f"{value}.\n\n"
        "Расчёт выполнен детерминированно "
        "на основе финансовых фактов.\n\n"
        f"Источники:\n{source_text}"
    )


def format_comparison(
    payload: dict,
) -> str:
    """
    Пользовательский ответ
    для сравнения компаний.
    """

    metric = metric_name(
        payload["metric"]
    )

    period = payload["period"]
    unit = payload["unit"]

    lines = [
        (
            f"{metric} за {period} год "
            "после приведения значений "
            "к одной денежной единице:"
        )
    ]

    for index, item in enumerate(
        payload["values"],
        start=1,
    ):
        company = company_name(
            item["company_id"]
        )

        value = format_value(
            value=item["value"],
            unit=unit,
        )

        source = format_source(
            item["source_fact"]
        )

        lines.append(
            f"{index}. {company} — "
            f"{value} {source}"
        )

    missing_companies = payload.get(
        "missing_companies",
        [],
    )

    if missing_companies:
        missing_text = ", ".join(
            company_name(company)
            for company in missing_companies
        )

        lines.append(
            "\nНет данных: "
            f"{missing_text}."
        )

    comparability = payload.get(
        "comparability"
    )

    if (
        comparability is not None
        and comparability.get(
            "status"
        )
        != "comparable"
    ):
        lines.append(
            "\nОговорка по сопоставимости: "
            + comparability["message"]
        )

    return "\n".join(
        lines
    )


def format_growth(
    payload: dict,
) -> str:
    """
    Пользовательский ответ
    для динамики показателя.
    """

    company = company_genitive_name(
        payload["company_id"]
    )

    metric_code = payload["metric"]

    metric = metric_name(
        metric_code
    )

    unit = payload["unit"]

    from_value = format_value(
        value=payload["from_value"],
        unit=unit,
    )

    to_value = format_value(
        value=payload["to_value"],
        unit=unit,
    )

    absolute_change = format_value(
        value=payload["absolute_change"],
        unit=unit,
    )

    growth_pct = Decimal(
        payload["growth_pct"]
    )

    growth_text = format_decimal(
        value=abs(growth_pct),
        decimal_places=2,
    )

    direction = growth_direction(
        metric=metric_code,
        growth_pct=growth_pct,
    )

    source_from = format_source(
        payload["sources"]["from"]
    )

    source_to = format_source(
        payload["sources"]["to"]
    )

    if growth_pct == 0:
        change_sentence = (
            f"{metric} {company} "
            f"{direction}: "
            f"{from_value}."
        )

    else:
        change_sentence = (
            f"{metric} {company} "
            f"{direction} на {growth_text}%: "
            f"с {from_value} в "
            f"{payload['from_period']} году "
            f"до {to_value} в "
            f"{payload['to_period']} году."
        )

    return (
        f"{change_sentence}\n\n"
        f"Абсолютное изменение: "
        f"{absolute_change}.\n\n"
        "Источники:\n"
        f"- {source_from}\n"
        f"- {source_to}"
    )


def format_dispatch_result(
    result: DispatchResult,
) -> str:
    """
    Превращает DispatchResult
    в финальный пользовательский ответ.
    """

    if (
        result.status
        == DispatchStatus.NEEDS_CLARIFICATION
    ):
        parsed = (
            result.parsed_question
        )

        if (
            parsed.from_period is None
            or parsed.to_period is None
        ) and (
            parsed.intent
            == QuestionIntent.GROWTH
        ):
            return (
                "Уточните, пожалуйста, периоды, "
                "между которыми нужно рассчитать "
                "изменение."
            )

        if parsed.period is None:
            return (
                "Уточните, пожалуйста, год "
                "для выполнения запроса."
            )

        return result.message

    if (
        result.status
        == DispatchStatus.UNSUPPORTED
    ):
        return (
            "Этот запрос пока нельзя выполнить "
            "доступными инструментами ассистента."
        )

    if (
        result.status
        == DispatchStatus.ERROR
    ):
        return (
            "Не удалось выполнить запрос: "
            f"{result.message}"
        )

    if result.payload is None:
        return result.message

    intent = (
        result.parsed_question.intent
    )

    if (
        intent
        == QuestionIntent.QUALITATIVE
    ):
        return str(
            result.payload["answer"]
        )

    if intent == QuestionIntent.FACT:
        return format_fact(
            result.payload
        )

    if (
        intent
        == QuestionIntent.DERIVED_METRIC
    ):
        return format_derived_metric(
            result.payload
        )

    if (
        intent
        == QuestionIntent.COMPARISON
    ):
        return format_comparison(
            result.payload
        )

    if intent == QuestionIntent.GROWTH:
        return format_growth(
            result.payload
        )

    return result.message