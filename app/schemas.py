from datetime import UTC, datetime
from enum import StrEnum

from pydantic import BaseModel, Field, field_validator, model_validator


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
    revenue: float | None = None
    previous_revenue: float | None = None
    net_income: float | None = None
    equity: float | None = None
    total_debt: float | None = None
    market_price: float | None = None
    earnings_per_share: float | None = None


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


class VerificationResult(BaseModel):
    passed: bool
    checks: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


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
    verification: VerificationResult | None = None
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


class AgentStepTrace(BaseModel):
    name: str
    status: str
    duration_ms: int = Field(ge=0)
    details: dict[str, str | int | float | bool] = Field(default_factory=dict)


class ModelUsageTrace(BaseModel):
    model: str
    input_tokens: int = Field(default=0, ge=0)
    output_tokens: int = Field(default=0, ge=0)
    estimated_cost_usd: float = Field(default=0, ge=0)


class AnalysisTrace(BaseModel):
    run_id: str
    ticker: str
    started_at: datetime
    completed_at: datetime | None = None
    status: RunStatus | None = None
    tool_calls: list[ToolCallTrace] = Field(default_factory=list)
    agent_steps: list[AgentStepTrace] = Field(default_factory=list)
    model_usage: list[ModelUsageTrace] = Field(default_factory=list)
    sources: list[str] = Field(default_factory=list)
    citations_count: int = Field(default=0, ge=0)
    latency_ms: int | None = Field(default=None, ge=0)
    estimated_cost_usd: float = Field(default=0, ge=0)
    error: str | None = None


class ObservabilitySummary(BaseModel):
    total_runs: int = Field(ge=0)
    answered_runs: int = Field(ge=0)
    insufficient_data_runs: int = Field(ge=0)
    tool_error_runs: int = Field(ge=0)
    answer_rate: float = Field(ge=0, le=1)
    average_latency_ms: float | None = Field(default=None, ge=0)
    total_estimated_cost_usd: float = Field(default=0, ge=0)
    average_cost_per_answered_run_usd: float | None = Field(default=None, ge=0)


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
    score: float | None = Field(default=None, ge=0)


class ExtractedField(BaseModel):
    name: str
    value: float
    currency: str = "BRL"
    citation: DocumentCitation


class DocumentRecord(BaseModel):
    id: str
    corpus_id: str
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
    document_ids: list[str] = Field(default_factory=list, max_length=50)
    corpus_id: str | None = Field(default=None, min_length=1, max_length=128)

    @field_validator("ticker")
    @classmethod
    def normalize_optional_ticker(cls, value: str | None) -> str | None:
        return AssetRequest.normalize_ticker(value) if value else None

    @field_validator("document_ids")
    @classmethod
    def deduplicate_document_ids(cls, value: list[str]) -> list[str]:
        return list(dict.fromkeys(item.strip() for item in value if item.strip()))

    @model_validator(mode="after")
    def require_research_scope(self) -> "DocumentResearchRequest":
        if not (self.document_id or self.document_ids or self.corpus_id or self.ticker):
            raise ValueError(
                "research requires document_id, document_ids, corpus_id or ticker to define a scope"
            )
        return self


class DocumentResearchResult(BaseModel):
    answer: str
    confidence: float = Field(ge=0, le=1)
    citations: list[DocumentCitation] = Field(min_length=1)
    retrieval_method: str = "hybrid"
