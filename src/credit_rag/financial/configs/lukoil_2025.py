from credit_rag.financial.layout_extraction import MetricLayoutRule
from credit_rag.financial.metrics import MetricCode
from credit_rag.financial.schemas import FinancialStandard

COMPANY_ID = "LUKOIL"
PERIOD = "2025"
DOC_ID = "lukoil_ifrs_2025"

STANDARD = FinancialStandard.IFRS
UNIT = "RUB_MILLION"


METRIC_RULES = (
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
    MetricLayoutRule(
        page_number=53,
        label_prefix="общий долг",
        metric=MetricCode.TOTAL_DEBT,
        start_x=400.0,
        end_x=500.0,
    ),
    MetricLayoutRule(
        page_number=53,
        label_prefix="минус денежные средства",
        metric=MetricCode.CASH_AND_EQUIVALENTS,
        start_x=400.0,
        end_x=500.0,
        use_absolute_value=True,
    ),
    MetricLayoutRule(
        page_number=53,
        label_prefix="чистый долг",
        metric=MetricCode.NET_DEBT,
        start_x=400.0,
        end_x=500.0,
    ),
    MetricLayoutRule(
        page_number=53,
        label_prefix="капитал",
        metric=MetricCode.TOTAL_EQUITY,
        start_x=400.0,
        end_x=500.0,
    ),
)