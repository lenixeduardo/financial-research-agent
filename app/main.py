from fastapi import FastAPI, Request, Response, status
from fastapi.responses import JSONResponse

from app.config import settings
from app.errors import AssetNotFoundError, ProviderTimeoutError
from app.observability import InMemoryTraceStore, finish_trace, start_trace
from app.schemas import AnalysisResult, AssetRequest, AnalysisTrace, ObservabilitySummary, RunStatus
from app.service import FinancialAnalysisService

app = FastAPI(title=settings.app_name, version=settings.app_version)
service = FinancialAnalysisService()
trace_store = InMemoryTraceStore()


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "version": settings.app_version}


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
