from decimal import Decimal
from enum import StrEnum

from pydantic import BaseModel, Field

from credit_rag.financial.metrics import MetricCode
from credit_rag.financial.units import UnitCode


class FinancialStandard(StrEnum):
    """
    Стандарт финансовой отчетности.
    """

    IFRS = "IFRS"
    RAS = "RAS"


class ExtractionMethod(StrEnum):
    """
    Способ извлечения финансового факта из документа.
    """

    MANUAL = "manual"
    TABLE = "table"
    XBRL = "xbrl"
    LLM = "llm"


class FinancialFact(BaseModel):
    """
    Представляет один проверяемый финансовый факт.
    """

    company_id: str
    period: str
    standard: FinancialStandard
    metric: MetricCode
    value: Decimal
    unit: UnitCode

    doc_id: str
    page: int = Field(ge=1)

    extraction_method: ExtractionMethod
    confidence: float = Field(ge=0.0, le=1.0)