from collections.abc import Sequence
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path

import pdfplumber

from credit_rag.financial.metrics import MetricCode
from credit_rag.financial.schemas import (
    ExtractionMethod,
    FinancialFact,
    FinancialStandard,
)

VALUE_START_X = 400.0
YEAR_SPLIT_X = 500.0


@dataclass(frozen=True)
class ExtractedMetricRow:
    """
    Представляет финансовую строку,
    извлеченную из layout PDF.
    """

    metric: MetricCode
    source_label: str
    value_2025: Decimal
    value_2024: Decimal

@dataclass(frozen=True)
class MetricLayoutRule:
    """
    Описывает правило извлечения одного показателя
    из layout финансового PDF.
    """

    page_number: int
    label_prefix: str
    metric: MetricCode
    start_x: float
    end_x: float | None
    use_absolute_value: bool = False
    line_span: int = 1
    value_line_offset: int = 0

def extract_metric_by_rule(
    pdf_path: Path,
    rule: MetricLayoutRule,
) -> tuple[MetricCode, Decimal]:
    """
    Извлекает один финансовый показатель
    по заранее определенному layout-правилу.

    Поддерживает показатели, название которых
    занимает несколько визуальных строк.
    """
    with pdfplumber.open(pdf_path) as pdf:
        page = pdf.pages[rule.page_number - 1]

        words = page.extract_words(
            x_tolerance=2,
            y_tolerance=2,
        )

    lines = group_words_into_lines(words)

    normalized_prefix = " ".join(
        rule.label_prefix.lower().split()
    )

    if rule.value_line_offset >= rule.line_span:
        raise ValueError(
            "value_line_offset должен быть меньше line_span."
        )

    for line_index in range(len(lines)):
        block = lines[
            line_index:
            line_index + rule.line_span
        ]

        if len(block) < rule.line_span:
            continue

        block_text = " ".join(
            " ".join(
                str(word["text"])
                for word in line
            )
            for line in block
        )

        normalized_block_text = " ".join(
            block_text.lower().split()
        )

        if not normalized_block_text.startswith(
            normalized_prefix
        ):
            continue

        value_line = block[
            rule.value_line_offset
        ]

        value = extract_column_value(
            line=value_line,
            start_x=rule.start_x,
            end_x=rule.end_x,
        )

        if rule.use_absolute_value:
            value = abs(value)

        return rule.metric, value

    raise ValueError(
        f"Не найдена метрика '{rule.label_prefix}' "
        f"на странице {rule.page_number}."
    )

def group_words_into_lines(
    words: list[dict],
    y_tolerance: float = 3.0,
) -> list[list[dict]]:
    """
    Группирует слова в визуальные строки
    по вертикальной координате.
    """
    sorted_words = sorted(
        words,
        key=lambda word: (
            float(word["top"]),
            float(word["x0"]),
        ),
    )

    lines: list[list[dict]] = []

    for word in sorted_words:
        if not lines:
            lines.append([word])
            continue

        current_line = lines[-1]

        current_top = sum(
            float(item["top"])
            for item in current_line
        ) / len(current_line)

        if abs(float(word["top"]) - current_top) <= y_tolerance:
            current_line.append(word)
        else:
            lines.append([word])

    for line in lines:
        line.sort(
            key=lambda word: float(word["x0"])
        )

    return lines


def parse_financial_number(
    value: str,
) -> Decimal:
    """
    Преобразует число из финансового PDF в Decimal.

    Скобки интерпретируются как отрицательное значение.
    """
    normalized = (
        value
        .replace("\xa0", "")
        .replace(" ", "")
        .strip()
    )

    is_negative = (
        normalized.startswith("(")
        and normalized.endswith(")")
    )

    normalized = (
        normalized
        .strip("()")
        .replace(",", ".")
        .replace("%", "")
    )

    number = Decimal(normalized)

    if is_negative:
        return -number

    return number


def extract_column_value(
    line: list[dict],
    start_x: float,
    end_x: float | None = None,
) -> Decimal:
    """
    Собирает числовое значение из слов,
    расположенных внутри заданной колонки.
    """
    tokens = []

    for word in line:
        x0 = float(word["x0"])

        if x0 < start_x:
            continue

        if end_x is not None and x0 >= end_x:
            continue

        tokens.append(
            str(word["text"])
        )

    if not tokens:
        raise ValueError(
            "Не удалось найти значение в числовой колонке."
        )

    raw_value = " ".join(tokens)

    return parse_financial_number(raw_value)


def extract_capital_table_rows(
    pdf_path: Path,
    page_number: int = 53,
) -> list[ExtractedMetricRow]:
    """
    Извлекает ключевые показатели из таблицы
    управления капиталом ЛУКОЙЛа.
    """
    row_rules = {
        "общий долг": (
            MetricCode.TOTAL_DEBT,
            False,
        ),
        "минус денежные средства": (
            MetricCode.CASH_AND_EQUIVALENTS,
            True,
        ),
        "чистый долг": (
            MetricCode.NET_DEBT,
            False,
        ),
        "капитал": (
            MetricCode.TOTAL_EQUITY,
            False,
        ),
    }

    with pdfplumber.open(pdf_path) as pdf:
        page = pdf.pages[page_number - 1]

        words = page.extract_words(
            x_tolerance=2,
            y_tolerance=2,
        )

    lines = group_words_into_lines(words)

    extracted_rows: list[ExtractedMetricRow] = []

    for line in lines:
        label_words = [
            str(word["text"])
            for word in line
            if float(word["x0"]) < VALUE_START_X
        ]

        label = " ".join(label_words)
        normalized_label = label.lower().strip()

        if normalized_label not in row_rules:
            continue

        metric, use_absolute_value = row_rules[
            normalized_label
        ]

        value_2025 = extract_column_value(
            line=line,
            start_x=VALUE_START_X,
            end_x=YEAR_SPLIT_X,
        )

        value_2024 = extract_column_value(
            line=line,
            start_x=YEAR_SPLIT_X,
        )

        if use_absolute_value:
            value_2025 = abs(value_2025)
            value_2024 = abs(value_2024)

        extracted_rows.append(
            ExtractedMetricRow(
                metric=metric,
                source_label=label,
                value_2025=value_2025,
                value_2024=value_2024,
            )
        )

    return extracted_rows

def build_financial_facts(
    rows: list[ExtractedMetricRow],
    company_id: str,
    period: str,
    doc_id: str,
    page_number: int,
    standard: FinancialStandard = FinancialStandard.IFRS,
    unit: str = "RUB_MILLION",
) -> list[FinancialFact]:
    """
    Преобразует автоматически извлеченные строки
    в типизированные финансовые факты.
    """
    facts: list[FinancialFact] = []

    for row in rows:
        if period == "2025":
            value = row.value_2025
        elif period == "2024":
            value = row.value_2024
        else:
            raise ValueError(
                f"Период {period} отсутствует "
                "в извлеченной таблице."
            )

        facts.append(
            FinancialFact(
                company_id=company_id,
                period=period,
                standard=standard,
                metric=row.metric,
                value=value,
                unit=unit,
                doc_id=doc_id,
                page=page_number,
                extraction_method=ExtractionMethod.TABLE,
                confidence=0.90,
            )
        )

    return facts

LUKOIL_2025_METRIC_RULES = (
    MetricLayoutRule(
        page_number=7,
        label_prefix=(
            "выручка от реализации "
            "(включая акцизы и экспортные пошлины)"
        ),
        metric=MetricCode.REVENUE,
        start_x=460.0,
        end_x=520.0,
    ),
    MetricLayoutRule(
        page_number=7,
        label_prefix="операционная прибыль",
        metric=MetricCode.OPERATING_PROFIT,
        start_x=460.0,
        end_x=520.0,
    ),
    MetricLayoutRule(
        page_number=9,
        label_prefix=(
            "чистые денежные средства, "
            "полученные от операционной деятельности"
        ),
        metric=MetricCode.OPERATING_CASH_FLOW,
        start_x=450.0,
        end_x=515.0,
    ),
    MetricLayoutRule(
        page_number=9,
        label_prefix="капитальные затраты",
        metric=MetricCode.CAPEX,
        start_x=450.0,
        end_x=515.0,
        use_absolute_value=True,
    ),
    MetricLayoutRule(
        page_number=46,
        label_prefix="ebitda",
        metric=MetricCode.EBITDA,
        start_x=520.0,
        end_x=None,
    ),
)

def extract_financial_facts(
    pdf_path: Path,
    rules: Sequence[MetricLayoutRule],
    company_id: str,
    period: str,
    doc_id: str,
    standard: FinancialStandard,
    unit: str,
) -> list[FinancialFact]:
    """
    Извлекает финансовые факты из PDF
    на основании конфигурации документа.
    """
    facts: list[FinancialFact] = []
    extracted_metrics: set[MetricCode] = set()

    for rule in rules:
        metric, value = extract_metric_by_rule(
            pdf_path=pdf_path,
            rule=rule,
        )

        if metric in extracted_metrics:
            raise ValueError(
                f"Метрика {metric.value} "
                "извлечена несколько раз."
            )

        facts.append(
            FinancialFact(
                company_id=company_id,
                period=period,
                standard=standard,
                metric=metric,
                value=value,
                unit=unit,
                doc_id=doc_id,
                page=rule.page_number,
                extraction_method=ExtractionMethod.TABLE,
                confidence=0.90,
            )
        )

        extracted_metrics.add(metric)

    return facts