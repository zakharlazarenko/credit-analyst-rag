import pytest

from credit_rag.financial.metrics import MetricCode
from credit_rag.financial.temporal_comparability import (
    TemporalComparabilityStatus,
    assess_temporal_comparability,
)


@pytest.mark.parametrize(
    (
        "company_id",
        "metric",
        "expected_status",
    ),
    [
        (
            "ROSNEFT",
            MetricCode.REVENUE,
            TemporalComparabilityStatus.COMPARABLE,
        ),
        (
            "TATNEFT",
            MetricCode.OPERATING_CASH_FLOW,
            TemporalComparabilityStatus.COMPARABLE,
        ),
        (
            "LUKOIL",
            MetricCode.REVENUE,
            TemporalComparabilityStatus.NOT_COMPARABLE,
        ),
        (
            "LUKOIL",
            MetricCode.EBITDA,
            TemporalComparabilityStatus.UNKNOWN,
        ),
    ],
)
def test_temporal_comparability_2024_to_2025(
    company_id: str,
    metric: MetricCode,
    expected_status: TemporalComparabilityStatus,
) -> None:
    result = assess_temporal_comparability(
        company_id=company_id,
        metric=metric,
        from_period="2024",
        to_period="2025",
    )

    assert result.status == expected_status
    assert result.message