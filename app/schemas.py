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


class RunStatus(StrEnum):
    ANSWERED = "answered"
    INSUFFICIENT_DATA = "insufficient_data"
    TOOL_ERROR = "tool_error"


class ToolCallTrace(BaseModel):
    name: str
    arguments: dict[str, str]
    status: str
    duration_ms: int = Field(ge=0)
    error: str | None = None


class AnalysisTrace(BaseModel):
    run_id: str
    ticker: str
    started_at: datetime
    completed_at: datetime | None = None
    status: RunStatus | None = None
    tool_calls: list[ToolCallTrace] = Field(default_factory=list)
    sources: list[str] = Field(default_factory=list)
    citations_count: int = Field(default=0, ge=0)
    latency_ms: int | None = Field(default=None, ge=0)
    error: str | None = None


class ObservabilitySummary(BaseModel):
    total_runs: int = Field(ge=0)
    answered_runs: int = Field(ge=0)
    insufficient_data_runs: int = Field(ge=0)
    tool_error_runs: int = Field(ge=0)
    answer_rate: float = Field(ge=0, le=1)
    average_latency_ms: float | None = Field(default=None, ge=0)


class DocumentType(StrEnum):
    FINANCIAL_STATEMENT = "financial_statement"
    FINANCIAL_REPORT = "financial_report"
    SPREADSHEET = "spreadsheet"
    UNKNOWN = "unknown"


class DocumentCitation(BaseModel):
    document_id: str
    document_name: str
    location: str
    excerpt: str


class ExtractedField(BaseModel):
    name: str
    value: float
    currency: str = "BRL"
    citation: DocumentCitation


class DocumentRecord(BaseModel):
    id: str
    name: str
    content_type: str
    ticker: str | None = None
    document_type: DocumentType
    page_count: int = Field(ge=1)
    chunk_count: int = Field(ge=1)
    extraction_confidence: float = Field(ge=0, le=1)
    extracted_fields: list[ExtractedField]
    source_sha256: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class DocumentResearchRequest(BaseModel):
    ticker: str | None = Field(default=None, min_length=2, max_length=12)
    question: str = Field(min_length=5, max_length=500)
    document_id: str | None = None

    @field_validator("ticker")
    @classmethod
    def normalize_optional_ticker(cls, value: str | None) -> str | None:
        return AssetRequest.normalize_ticker(value) if value else None


class DocumentResearchResult(BaseModel):
    answer: str
    confidence: float = Field(ge=0, le=1)
    citations: list[DocumentCitation] = Field(min_length=1)
