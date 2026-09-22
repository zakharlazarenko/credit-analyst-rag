from credit_rag.financial.comparability import (
    ComparabilityStatus,
    assess_comparability,
)
from credit_rag.financial.metrics import MetricCode


def test_revenue_comparison_requires_caution() -> None:
    result = assess_comparability(
        companies=(
            "LUKOIL",
            "ROSNEFT",
            "TATNEFT",
        ),
        metric=MetricCode.REVENUE,
    )

    assert result.metric == MetricCode.REVENUE
    assert result.status == ComparabilityStatus.CAUTION

    assert result.message