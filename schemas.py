from datetime import UTC, datetime
from enum import StrEnum

from pydantic import BaseModel, Field, field_validator


class MetricStatus(StrEnum):
    POSITIVE = "positive"
    NEUTRAL = "neutral"
    NEGATIVE = "negative"
    UNKNOWN = "unknown"


class RiskSeverity(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class AnalysisType(StrEnum):
    FUNDAMENTAL = "fundamental"


class AssetRequest(BaseModel):
    ticker: str = Field(min_length=2, max_length=12, examples=["PETR4"])
    analysis_type: AnalysisType = AnalysisType.FUNDAMENTAL

    @field_validator("ticker")
    @classmethod
    def normalize_ticker(cls, value: str) -> str:
        ticker = value.strip().upper()
        if not ticker.replace(".", "").isalnum():
            raise ValueError("ticker must contain only letters, numbers or a dot")
        return ticker


class CompanyProfile(BaseModel):
    ticker: str
    company_name: str
    currency: str = "BRL"
    sector: str


class FinancialSnapshot(BaseModel):
    revenue: float
    previous_revenue: float
    net_income: float
    equity: float
    total_debt: float
    market_price: float
    earnings_per_share: float


class FinancialMetric(BaseModel):
    name: str
    value: float | None
    unit: str | None = None
    interpretation: str
    status: MetricStatus


class RiskSignal(BaseModel):
    category: str
    description: str
    severity: RiskSeverity
    evidence: str


class DataSource(BaseModel):
    provider: str
    reference: str
    retrieved_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    is_mock: bool = True


class AnalysisResult(BaseModel):
    ticker: str
    company_name: str
    summary: str
    metrics: list[FinancialMetric]
    risks: list[RiskSignal]
    positive_signals: list[str]
    missing_information: list[str]
    sources: list[DataSource]
    confidence: float = Field(ge=0, le=1)
    disclaimer: str = "Conteúdo educacional; não constitui recomendação de investimento."

