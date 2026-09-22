from credit_rag.financial.layout_extraction import MetricLayoutRule
from credit_rag.financial.metrics import MetricCode
from credit_rag.financial.schemas import FinancialStandard

COMPANY_ID = "ROSNEFT"
PERIOD = "2025"
DOC_ID = "rosneft_ifrs_2025"

STANDARD = FinancialStandard.IFRS
UNIT = "RUB_BILLION"


METRIC_RULES = (
    MetricLayoutRule(
        page_number=5,
        label_prefix="итого активы",
        metric=MetricCode.TOTAL_ASSETS,
        start_x=400.0,
        end_x=470.0,
    ),
    MetricLayoutRule(
        page_number=5,
        label_prefix="итого капитал",
        metric=MetricCode.TOTAL_EQUITY,
        start_x=400.0,
        end_x=470.0,
    ),
    MetricLayoutRule(
        page_number=6,
        label_prefix=(
            "итого выручка от реализации и доход от "
            "ассоциированных организаций и совместных предприятий"
        ),
        metric=MetricCode.REVENUE,
        start_x=400.0,
        end_x=470.0,
        line_span=3,
        value_line_offset=2,
    ),
    MetricLayoutRule(
        page_number=6,
        label_prefix="операционная прибыль",
        metric=MetricCode.OPERATING_PROFIT,
        start_x=400.0,
        end_x=470.0,
    ),
)