from fastapi import FastAPI, File, Form, Request, Response, UploadFile, status
from fastapi.responses import JSONResponse

from app.config import settings
from app.documents import InMemoryDocumentStore, ingest_document
from app.errors import (
    AssetNotFoundError,
    DocumentNotFoundError,
    InsufficientEvidenceError,
    ProviderTimeoutError,
    SecurityPolicyError,
    UnsupportedDocumentError,
)
from app.guardrails import assess_research_question, validate_document_size
from app.observability import InMemoryTraceStore, finish_trace, start_trace
from app.schemas import (
    AnalysisResult,
    AnalysisTrace,
    AssetRequest,
    DocumentRecord,
    DocumentResearchRequest,
    DocumentResearchResult,
    ObservabilitySummary,
    RunStatus,
)
from app.service import FinancialAnalysisService

app = FastAPI(title=settings.app_name, version=settings.app_version)
service = FinancialAnalysisService()
trace_store = InMemoryTraceStore()
document_store = InMemoryDocumentStore()


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "version": settings.app_version}


@app.get("/system/capabilities")
async def capabilities() -> dict[str, object]:
    return {
        "provider": settings.financial_provider,
        "hybrid_retrieval": True,
        "model_routing": True,
        "verification": True,
        "cost_tracking": True,
        "prompt_injection_guardrails": True,
        "supported_documents": ["pdf", "csv", "txt", "md", "xlsx"],
    }


@app.post("/analyses", response_model=AnalysisResult)
async def create_analysis(
    payload: AssetRequest, request: Request, response: Response
) -> AnalysisResult:
    trace, started_at = start_trace(payload.ticker)
    request.state.run_id = trace.run_id
    try:
        result = await service.analyze(payload.ticker, trace)
    except AssetNotFoundError as exc:
        finish_trace(trace, started_at=started_at, status=RunStatus.INSUFFICIENT_DATA, error=exc)
        trace_store.save(trace)
        raise
    except ProviderTimeoutError as exc:
        finish_trace(trace, started_at=started_at, status=RunStatus.TOOL_ERROR, error=exc)
        trace_store.save(trace)
        raise
    else:
        finish_trace(
            trace,
            started_at=started_at,
            status=RunStatus.ANSWERED,
            sources=[source.reference for source in result.sources],
        )
        trace_store.save(trace)
        response.headers["X-Run-ID"] = trace.run_id
        return result


@app.get("/observability/runs", response_model=list[AnalysisTrace])
async def list_runs() -> list[AnalysisTrace]:
    return trace_store.list()


@app.get("/observability/summary", response_model=ObservabilitySummary)
async def observability_summary() -> ObservabilitySummary:
    return trace_store.summary()


@app.post("/documents", response_model=DocumentRecord, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...), ticker: str | None = Form(default=None)
) -> DocumentRecord:
    normalized_ticker = AssetRequest.normalize_ticker(ticker) if ticker else None
    data = await file.read()
    validate_document_size(data)
    stored = ingest_document(
        name=file.filename or "uploaded-document",
        content_type=file.content_type or "application/octet-stream",
        data=data,
        ticker=normalized_ticker,
    )
    return document_store.save(stored)


@app.get("/documents", response_model=list[DocumentRecord])
async def list_documents() -> list[DocumentRecord]:
    return document_store.list()


@app.get("/documents/{document_id}", response_model=DocumentRecord)
async def get_document(document_id: str) -> DocumentRecord:
    return document_store.get(document_id).record


@app.post("/research", response_model=DocumentResearchResult)
async def research_documents(payload: DocumentResearchRequest) -> DocumentResearchResult:
    allowed, reasons = assess_research_question(payload.question)
    if not allowed:
        raise SecurityPolicyError(f"research question blocked by guardrail: {','.join(reasons)}")
    return document_store.search(payload)


@app.exception_handler(AssetNotFoundError)
async def asset_not_found_handler(request: Request, exc: AssetNotFoundError) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        headers={"X-Run-ID": getattr(request.state, "run_id", "")},
        content={"error": "asset_not_found", "detail": str(exc)},
    )


@app.exception_handler(ProviderTimeoutError)
async def provider_timeout_handler(request: Request, exc: ProviderTimeoutError) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_504_GATEWAY_TIMEOUT,
        headers={"X-Run-ID": getattr(request.state, "run_id", "")},
        content={"error": "provider_timeout", "detail": str(exc)},
    )


@app.exception_handler(DocumentNotFoundError)
async def document_not_found_handler(request: Request, exc: DocumentNotFoundError) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={"error": "document_not_found", "detail": str(exc)},
    )


@app.exception_handler(UnsupportedDocumentError)
async def unsupported_document_handler(request: Request, exc: UnsupportedDocumentError) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
        content={"error": "unsupported_document", "detail": str(exc)},
    )


@app.exception_handler(InsufficientEvidenceError)
async def insufficient_evidence_handler(request: Request, exc: InsufficientEvidenceError) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"error": "insufficient_evidence", "detail": str(exc)},
    )


@app.exception_handler(SecurityPolicyError)
async def security_policy_handler(request: Request, exc: SecurityPolicyError) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"error": "security_policy", "detail": str(exc)},
    )
