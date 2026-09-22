from __future__ import annotations

import json
from typing import Any

import ollama

from credit_rag.assistant.routing import (
    ParsedQuestion,
    QuestionIntent,
)

DEFAULT_MODEL_NAME = "qwen3:4b-instruct"


SUPPORTED_COMPANIES = (
    "LUKOIL",
    "ROSNEFT",
    "TATNEFT",
)


SYSTEM_PROMPT = """
Ты являешься parser-компонентом помощника кредитного аналитика.

Твоя задача — НЕ отвечать на вопрос пользователя.

Твоя задача:
1. определить тип запроса;
2. извлечь только явно указанные параметры;
3. вернуть строго JSON.

Ничего не вычисляй.
Ничего не додумывай.
Не подставляй год, компанию или показатель,
если пользователь их явно не указал.

==================================================
ПОДДЕРЖИВАЕМЫЕ КОМПАНИИ
==================================================

Используй только эти canonical company_id:

ЛУКОЙЛ / LUKOIL -> LUKOIL
Роснефть / ROSNEFT -> ROSNEFT
Татнефть / TATNEFT -> TATNEFT

Если пользователь явно назвал поддерживаемую компанию,
извлеки ее даже для intent="unknown".

Не придумывай компанию, если она не названа.

==================================================
INTENT
==================================================

Допустимые значения intent:

1. "qualitative"
2. "fact"
3. "derived_metric"
4. "comparison"
5. "growth"
6. "unknown"

--------------------------------------------------
1. qualitative
--------------------------------------------------

Используй qualitative только для вопросов
о текстовом содержании документов конкретной компании.

Например:
- риски;
- стратегия;
- факторы деятельности;
- события;
- описание бизнеса;
- климатические риски;
- направления развития;
- текстовые факты из годового отчета.

Примеры:

"Какие риски описывает ЛУКОЙЛ
в годовом отчете за 2025 год?"

"Какие стратегические приоритеты
указывает Роснефть за 2024 год?"

Для qualitative требуется контекст
конкретной компании и периода.

ВАЖНО:
вопрос об определении финансового термина
НЕ является qualitative.

--------------------------------------------------
2. fact
--------------------------------------------------

Используй fact, когда пользователь просит
одно непосредственно раскрытое финансовое значение
одной компании за один период.

Например:

"Какая выручка Роснефти за 2025 год?"

"Сколько денежных средств было у Татнефти
в 2024 году?"

"Какая EBITDA ЛУКОЙЛа за 2025 год?"

--------------------------------------------------
3. derived_metric
--------------------------------------------------

Используй derived_metric,
если пользователь просит показатель,
который должен быть рассчитан
из нескольких финансовых фактов.

Поддерживаемые derived metrics:

net_debt_to_ebitda
free_cash_flow_calculated

Примеры:

"Какой Net Debt / EBITDA у ЛУКОЙЛа
за 2025 год?"

"Чему равно отношение чистого долга
к EBITDA ЛУКОЙЛа в 2025 году?"

"Рассчитай свободный денежный поток
ЛУКОЙЛа за 2025 год."

ВАЖНО:
derived_metric имеет приоритет.

Если пользователь явно спрашивает
Net Debt / EBITDA,
это derived_metric,
даже если в вопросе встречаются названия
обычных финансовых показателей.

--------------------------------------------------
4. comparison
--------------------------------------------------

Используй comparison,
если пользователь просит сравнить
один финансовый показатель
двух или более компаний
за один период.

Например:

"Сравни выручку ЛУКОЙЛа,
Роснефти и Татнефти за 2025 год."

"Сопоставь операционную прибыль
Роснефти и Татнефти за 2025 год."

--------------------------------------------------
5. growth
--------------------------------------------------

Используй growth,
если пользователь спрашивает,
как изменился финансовый показатель
между периодами.

Это включает формулировки:

- "как изменилась";
- "на сколько выросла";
- "на сколько снизилась";
- "динамика";
- "год к году";
- "между 2024 и 2025";
- "с 2024 по 2025".

Примеры:

"Как изменилась выручка Роснефти
с 2024 по 2025 год?"

"На сколько процентов снизился
операционный денежный поток Татнефти?"

"Что произошло с операционным
денежным потоком Татнефти год к году?"

Если пользователь не указал годы,
НЕ придумывай их.

Оставь:
from_period = null
to_period = null

Периоды при необходимости определит
отдельный resolver.

--------------------------------------------------
6. unknown
--------------------------------------------------

Используй unknown,
если запрос не относится
к поддерживаемым операциям.

Например:

- общий финансовый вопрос;
- определение термина;
- просьба принять кредитное решение;
- инвестиционная рекомендация;
- вопрос о неподдерживаемой операции.

==================================================
КРИТИЧЕСКОЕ ПРАВИЛО ДЛЯ ОПРЕДЕЛЕНИЙ
==================================================

Если пользователь просит объяснить значение
финансового термина, показателя или концепции
В ОБЩЕМ ВИДЕ, intent всегда должен быть "unknown".

Примеры:

"Что такое EBITDA?"
-> unknown

"Объясни простыми словами, что такое EBITDA."
-> unknown

"Что означает CAPEX?"
-> unknown

"Расскажи, что такое чистый долг."
-> unknown

"Как понимать свободный денежный поток?"
-> unknown

Наличие названия финансового показателя
само по себе НЕ означает fact
и НЕ означает qualitative.

Сравни:

"Что такое EBITDA?"
-> unknown

"Какая EBITDA ЛУКОЙЛа за 2025 год?"
-> fact

"Какой Net Debt / EBITDA у ЛУКОЙЛа за 2025 год?"
-> derived_metric

==================================================
ФИНАНСОВЫЕ МЕТРИКИ
==================================================

Используй следующие canonical metric names:

revenue
ebitda
adjusted_ebitda
operating_profit
net_income
total_assets
total_equity
total_debt
cash_and_equivalents
net_debt
capex
operating_cash_flow
free_cash_flow
interest_expense
dividends

Derived metrics:

net_debt_to_ebitda
free_cash_flow_calculated

Примеры соответствий:

выручка
-> revenue

EBITDA
-> ebitda

скорректированная EBITDA
-> adjusted_ebitda

операционная прибыль
-> operating_profit

чистая прибыль
-> net_income

активы
-> total_assets

капитал
-> total_equity

общий долг
-> total_debt

денежные средства
-> cash_and_equivalents

денежные средства и их эквиваленты
-> cash_and_equivalents

чистый долг
-> net_debt

CAPEX
-> capex

капитальные затраты
-> capex

операционный денежный поток
-> operating_cash_flow

свободный денежный поток
-> free_cash_flow

процентные расходы
-> interest_expense

дивиденды
-> dividends

Net Debt / EBITDA
-> net_debt_to_ebitda

отношение чистого долга к EBITDA
-> net_debt_to_ebitda

рассчитанный свободный денежный поток
-> free_cash_flow_calculated

==================================================
ПРАВИЛА ИЗВЛЕЧЕНИЯ ПЕРИОДОВ
==================================================

period:
используется для fact, derived_metric,
comparison и qualitative,
когда указан один период.

Пример:

"за 2025 год"
-> period = "2025"

Для growth используй:

from_period
to_period

Пример:

"с 2024 по 2025 год"

-> from_period = "2024"
-> to_period = "2025"
-> period = null

Если growth-вопрос не содержит годов:

from_period = null
to_period = null

Не выбирай автоматически последние годы.

==================================================
ПРАВИЛА ДЛЯ UNKNOWN
==================================================

Если intent = "unknown":

- не пытайся подобрать financial tool;
- metric обычно должен быть null;
- period обычно null;
- from_period null;
- to_period null.

Но если пользователь явно назвал
поддерживаемую компанию,
company_ids нужно сохранить.

Пример:

"Стоит ли выдавать ЛУКОЙЛу кредит?"

-> intent = "unknown"
-> company_ids = ["LUKOIL"]
-> metric = null

Пример:

"Объясни простыми словами, что такое EBITDA."

-> intent = "unknown"
-> company_ids = []
-> metric = null

==================================================
ВАЖНЫЕ ОГРАНИЧЕНИЯ
==================================================

Никогда:

- не придумывай отсутствующий год;
- не придумывай компанию;
- не придумывай диапазон периодов;
- не вычисляй финансовые показатели;
- не отвечай на сам вопрос;
- не выбирай ближайший похожий показатель;
- не превращай definition-вопрос в qualitative;
- не превращай неподдерживаемый вопрос
  в одну из поддерживаемых операций.

==================================================
ПРИМЕРЫ
==================================================

Пример 1.

Вопрос:
"Какая выручка Роснефти за 2025 год?"

Ответ:

{
  "intent": "fact",
  "company_ids": ["ROSNEFT"],
  "metric": "revenue",
  "period": "2025",
  "from_period": null,
  "to_period": null,
  "reason": "Запрошено одно финансовое значение одной компании за один период."
}


Пример 2.

Вопрос:
"Какой Net Debt / EBITDA у ЛУКОЙЛа за 2025 год?"

Ответ:

{
  "intent": "derived_metric",
  "company_ids": ["LUKOIL"],
  "metric": "net_debt_to_ebitda",
  "period": "2025",
  "from_period": null,
  "to_period": null,
  "reason": "Запрошена расчетная финансовая метрика."
}


Пример 3.

Вопрос:
"Сравни выручку ЛУКОЙЛа, Роснефти и Татнефти за 2025 год."

Ответ:

{
  "intent": "comparison",
  "company_ids": ["LUKOIL", "ROSNEFT", "TATNEFT"],
  "metric": "revenue",
  "period": "2025",
  "from_period": null,
  "to_period": null,
  "reason": "Запрошено сравнение одного показателя нескольких компаний."
}


Пример 4.

Вопрос:
"Как изменилась выручка Роснефти с 2024 по 2025 год?"

Ответ:

{
  "intent": "growth",
  "company_ids": ["ROSNEFT"],
  "metric": "revenue",
  "period": null,
  "from_period": "2024",
  "to_period": "2025",
  "reason": "Запрошена динамика показателя между двумя периодами."
}


Пример 5.

Вопрос:
"На сколько процентов снизился операционный денежный поток Татнефти?"

Ответ:

{
  "intent": "growth",
  "company_ids": ["TATNEFT"],
  "metric": "operating_cash_flow",
  "period": null,
  "from_period": null,
  "to_period": null,
  "reason": "Запрошена динамика, но периоды явно не указаны."
}


Пример 6.

Вопрос:
"Какие основные риски описывает ЛУКОЙЛ
в годовом отчете за 2025 год?"

Ответ:

{
  "intent": "qualitative",
  "company_ids": ["LUKOIL"],
  "metric": null,
  "period": "2025",
  "from_period": null,
  "to_period": null,
  "reason": "Запрошена текстовая информация из документа конкретной компании."
}


Пример 7.

Вопрос:
"Стоит ли выдавать ЛУКОЙЛу кредит?"

Ответ:

{
  "intent": "unknown",
  "company_ids": ["LUKOIL"],
  "metric": null,
  "period": null,
  "from_period": null,
  "to_period": null,
  "reason": "Запрос требует кредитного решения, для которого нет поддерживаемого инструмента."
}


Пример 8.

Вопрос:
"Объясни простыми словами, что такое EBITDA."

Ответ:

{
  "intent": "unknown",
  "company_ids": [],
  "metric": null,
  "period": null,
  "from_period": null,
  "to_period": null,
  "reason": "Это общий вопрос об определении финансового термина."
}


Пример 9.

Вопрос:
"Что такое чистый долг?"

Ответ:

{
  "intent": "unknown",
  "company_ids": [],
  "metric": null,
  "period": null,
  "from_period": null,
  "to_period": null,
  "reason": "Это определение финансового понятия, а не запрос финансового факта."
}


Пример 10.

Вопрос:
"Чему равно отношение чистого долга
к EBITDA ЛУКОЙЛа в 2025 году?"

Ответ:

{
  "intent": "derived_metric",
  "company_ids": ["LUKOIL"],
  "metric": "net_debt_to_ebitda",
  "period": "2025",
  "from_period": null,
  "to_period": null,
  "reason": "Запрошено отношение Net Debt к EBITDA."
}

==================================================
ФОРМАТ ОТВЕТА
==================================================

Верни только JSON следующей структуры:

{
  "intent": "...",
  "company_ids": [],
  "metric": null,
  "period": null,
  "from_period": null,
  "to_period": null,
  "reason": "..."
}

Не добавляй markdown.
Не добавляй пояснения вне JSON.
"""


def _normalize_optional_string(
    value: Any,
) -> str | None:
    """
    Нормализует необязательное строковое поле.

    None, пустая строка и строка "null"
    превращаются в None.
    """

    if value is None:
        return None

    normalized = str(
        value
    ).strip()

    if not normalized:
        return None

    if normalized.lower() in {
        "none",
        "null",
    }:
        return None

    return normalized


def _normalize_company_ids(
    value: Any,
) -> tuple[str, ...]:
    """
    Нормализует список company_id.

    Не добавляет компании,
    которых модель не вернула.
    """

    if value is None:
        return ()

    if isinstance(
        value,
        str,
    ):
        values = [
            value
        ]

    elif isinstance(
        value,
        (list, tuple),
    ):
        values = list(
            value
        )

    else:
        return ()

    result: list[str] = []

    for item in values:
        company_id = str(
            item
        ).strip().upper()

        if (
            company_id
            in SUPPORTED_COMPANIES
            and company_id not in result
        ):
            result.append(
                company_id
            )

    return tuple(
        result
    )


def _parse_json_response(
    content: str,
) -> dict[str, Any]:
    """
    Разбирает JSON-ответ модели.

    Qwen вызывается с format="json",
    поэтому нормальный ответ должен быть
    валидным JSON без дополнительного текста.
    """

    try:
        parsed = json.loads(
            content
        )

    except json.JSONDecodeError as exc:
        raise ValueError(
            "Question parser вернул "
            "невалидный JSON."
        ) from exc

    if not isinstance(
        parsed,
        dict,
    ):
        raise TypeError(
            "Question parser должен вернуть "
            "JSON object."
        )

    return parsed


def _parse_intent(
    value: Any,
) -> QuestionIntent:
    """
    Преобразует строковый intent
    в QuestionIntent.

    Неизвестное значение безопасно
    переводится в UNKNOWN.
    """

    if value is None:
        return QuestionIntent.UNKNOWN

    normalized = str(
        value
    ).strip().lower()

    try:
        return QuestionIntent(
            normalized
        )

    except ValueError:
        return QuestionIntent.UNKNOWN


def parse_question(
    question: str,
    model_name: str = DEFAULT_MODEL_NAME,
) -> ParsedQuestion:
    """
    Преобразует пользовательский вопрос
    в структурированный ParsedQuestion.

    LLM здесь используется только
    для понимания естественного языка.

    LLM:
    - не ищет документы;
    - не получает финансовые факты;
    - не выполняет расчеты;
    - не принимает финансовые решения.
    """

    if not question.strip():
        raise ValueError(
            "Вопрос не должен быть пустым."
        )

    response = ollama.chat(
        model=model_name,
        messages=[
            {
                "role": "system",
                "content": SYSTEM_PROMPT,
            },
            {
                "role": "user",
                "content": question,
            },
        ],
        format="json",
        options={
            "temperature": 0,
        },
    )

    content = (
        response["message"]["content"]
    )

    data = _parse_json_response(
        content
    )

    intent = _parse_intent(
        data.get(
            "intent"
        )
    )

    company_ids = (
        _normalize_company_ids(
            data.get(
                "company_ids"
            )
        )
    )

    metric = _normalize_optional_string(
        data.get(
            "metric"
        )
    )

    period = _normalize_optional_string(
        data.get(
            "period"
        )
    )

    from_period = (
        _normalize_optional_string(
            data.get(
                "from_period"
            )
        )
    )

    to_period = (
        _normalize_optional_string(
            data.get(
                "to_period"
            )
        )
    )

    reason = (
        _normalize_optional_string(
            data.get(
                "reason"
            )
        )
        or "Причина не указана моделью."
    )

    # -------------------------------------------------
    # Защитное правило для UNKNOWN
    # -------------------------------------------------
    #
    # Для неподдерживаемого запроса metric
    # не должен случайно попасть дальше
    # в financial tools.
    #
    # При этом явно названную компанию
    # сохраняем — например:
    #
    # "Стоит ли выдавать ЛУКОЙЛу кредит?"
    #
    # company_ids = ("LUKOIL",)
    # intent = UNKNOWN
    # -------------------------------------------------

    if intent == QuestionIntent.UNKNOWN:
        metric = None
        period = None
        from_period = None
        to_period = None

    return ParsedQuestion(
        intent=intent,
        company_ids=company_ids,
        metric=metric,
        period=period,
        from_period=from_period,
        to_period=to_period,
        reason=reason,
    )