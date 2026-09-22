from credit_rag.financial.layout_extraction import MetricLayoutRule
from credit_rag.financial.metrics import MetricCode
from credit_rag.financial.schemas import FinancialStandard
from credit_rag.financial.units import UnitCode

COMPANY_ID = "TATNEFT"
PERIOD = "2025"
DOC_ID = "tatneft_ifrs_2025"

STANDARD = FinancialStandard.IFRS
UNIT = UnitCode.RUB_MILLION


METRIC_RULES = (
    MetricLayoutRule(
        page_number=9,
        label_prefix="выручка от реализации (без финансовых услуг)",
        metric=MetricCode.REVENUE,
        start_x=410,
        end_x=490,
    ),

    MetricLayoutRule(
        page_number=9,
        label_prefix="операционная прибыль (без финансовых услуг)",
        metric=MetricCode.OPERATING_PROFIT,
        start_x=410,
        end_x=490,
    ),

    MetricLayoutRule(
        page_number=13,
        label_prefix=(
            "чистые денежные средства, полученные "
            "от операционной деятельности"
        ),
        metric=MetricCode.OPERATING_CASH_FLOW,
        start_x=420,
        end_x=490,
        line_span=2,
        value_line_offset=1,
    ),

    MetricLayoutRule(
        page_number=14,
        label_prefix="итого денежные средства и их эквиваленты",
        metric=MetricCode.CASH_AND_EQUIVALENTS,
        start_x=400,
        end_x=480,
    ),
)