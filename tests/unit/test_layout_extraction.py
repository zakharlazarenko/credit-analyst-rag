from decimal import Decimal

import pytest

from credit_rag.financial.layout_extraction import (
    ExtractedMetricRow,
    build_financial_facts,
    extract_column_value,
    group_words_into_lines,
    parse_financial_number,
)
from credit_rag.financial.metrics import MetricCode
from credit_rag.financial.schemas import (
    ExtractionMethod,
    FinancialStandard,
)
from credit_rag.financial.units import UnitCode


@pytest.mark.parametrize(
    ("raw_value", "expected"),
    [
        ("1 234", Decimal(1234)),
        ("1 234,56", Decimal("1234.56")),
        ("(500)", Decimal(-500)),
        ("12,5%", Decimal("12.5")),
    ],
)
def test_parse_financial_number(
    raw_value: str,
    expected: Decimal,
) -> None:
    assert (
        parse_financial_number(raw_value)
        == expected
    )


def test_group_words_into_lines() -> None:
    words = [
        {
            "text": "Выручка",
            "x0": 10.0,
            "top": 100.0,
        },
        {
            "text": "100",
            "x0": 450.0,
            "top": 101.0,
        },
        {
            "text": "EBITDA",
            "x0": 10.0,
            "top": 120.0,
        },
        {
            "text": "25",
            "x0": 450.0,
            "top": 121.0,
        },
    ]

    lines = group_words_into_lines(
        words,
        y_tolerance=3.0,
    )

    assert len(lines) == 2

    assert [
        word["text"]
        for word in lines[0]
    ] == [
        "Выручка",
        "100",
    ]

    assert [
        word["text"]
        for word in lines[1]
    ] == [
        "EBITDA",
        "25",
    ]


def test_extract_column_value() -> None:
    line = [
        {
            "text": "Выручка",
            "x0": 20.0,
        },
        {
            "text": "1",
            "x0": 450.0,
        },
        {
            "text": "234",
            "x0": 470.0,
        },
        {
            "text": "999",
            "x0": 530.0,
        },
    ]

    result = extract_column_value(
        line=line,
        start_x=400.0,
        end_x=500.0,
    )

    assert result == Decimal(1234)


def test_build_financial_facts() -> None:
    rows = [
        ExtractedMetricRow(
            metric=MetricCode.TOTAL_DEBT,
            source_label="Общий долг",
            value_2025=Decimal(318012),
            value_2024=Decimal(380006),
        ),
        ExtractedMetricRow(
            metric=MetricCode.NET_DEBT,
            source_label="Чистый долг",
            value_2025=Decimal(-225803),
            value_2024=Decimal(-1046258),
        ),
    ]

    facts = build_financial_facts(
        rows=rows,
        company_id="LUKOIL",
        period="2025",
        doc_id="lukoil_ifrs_2025",
        page_number=53,
        standard=FinancialStandard.IFRS,
        unit="RUB_MILLION",
    )

    assert len(facts) == 2

    assert facts[0].metric == MetricCode.TOTAL_DEBT
    assert facts[0].value == Decimal(318012)
    assert facts[0].unit == UnitCode.RUB_MILLION

    assert facts[1].metric == MetricCode.NET_DEBT
    assert facts[1].value == Decimal(-225803)

    assert all(
        fact.extraction_method
        == ExtractionMethod.TABLE
        for fact in facts
    )


def test_build_financial_facts_rejects_unknown_period() -> None:
    rows = [
        ExtractedMetricRow(
            metric=MetricCode.REVENUE,
            source_label="Выручка",
            value_2025=Decimal(100),
            value_2024=Decimal(90),
        )
    ]

    with pytest.raises(
        ValueError,
        match="Период 2023",
    ):
        build_financial_facts(
            rows=rows,
            company_id="TEST",
            period="2023",
            doc_id="test_document",
            page_number=1,
        )