from credit_rag.financial.layout_extraction import MetricLayoutRule
from credit_rag.financial.metrics import MetricCode
from credit_rag.financial.schemas import FinancialStandard
from credit_rag.financial.units import UnitCode

COMPANY_ID = "LUKOIL"
PERIOD = "2024"
DOC_ID = "lukoil_ifrs_2024"

STANDARD = FinancialStandard.IFRS
UNIT = UnitCode.RUB_MILLION


METRIC_RULES = (
    MetricLayoutRule(
        page_number=7,
        label_prefix=(
            "выручка от реализации "
            "(включая акцизы и экспортные пошлины)"
        ),
        metric=MetricCode.REVENUE,
        start_x=430,
        end_x=510,
    ),

    MetricLayoutRule(
        page_number=7,
        label_prefix="операционная прибыль",
        metric=MetricCode.OPERATING_PROFIT,
        start_x=430,
        end_x=510,
    ),

    MetricLayoutRule(
        page_number=9,
        label_prefix=(
            "чистые денежные средства, полученные "
            "от операционной деятельности"
        ),
        metric=MetricCode.OPERATING_CASH_FLOW,
        start_x=430,
        end_x=510,
    ),

    MetricLayoutRule(
        page_number=9,
        label_prefix="капитальные затраты",
        metric=MetricCode.CAPEX,
        start_x=430,
        end_x=510,
        use_absolute_value=True,
    ),

    MetricLayoutRule(
        page_number=42,
        label_prefix="ebitda",
        metric=MetricCode.EBITDA,
        start_x=510,
        end_x=None,
    ),

    MetricLayoutRule(
        page_number=6,
        label_prefix="денежные средства и их эквиваленты",
        metric=MetricCode.CASH_AND_EQUIVALENTS,
        start_x=425,
        end_x=510,
    ),

    MetricLayoutRule(
        page_number=49,
        label_prefix="чистый долг",
        metric=MetricCode.NET_DEBT,
        start_x=420,
        end_x=510,
    ),

    MetricLayoutRule(
        page_number=6,
        label_prefix="итого капитал",
        metric=MetricCode.TOTAL_EQUITY,
        start_x=425,
        end_x=510,
    ),
)