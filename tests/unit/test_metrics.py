import pytest

from credit_rag.financial.metrics import (
    MetricCode,
    resolve_metric,
)


@pytest.mark.parametrize(
    ("raw_metric", "expected"),
    [
        (
            "Выручка",
            MetricCode.REVENUE,
        ),
        (
            "revenue",
            MetricCode.REVENUE,
        ),
        (
            "FCF",
            MetricCode.FREE_CASH_FLOW,
        ),
        (
            "чистый долг",
            MetricCode.NET_DEBT,
        ),
        (
            "Adjusted EBITDA",
            MetricCode.ADJUSTED_EBITDA,
        ),
        (
            "операционная прибыль",
            MetricCode.OPERATING_PROFIT,
        ),
        (
            "неизвестный показатель",
            None,
        ),
    ],
)
def test_resolve_metric(
    raw_metric: str,
    expected: MetricCode | None,
) -> None:
    result = resolve_metric(
        raw_metric
    )

    assert result == expected