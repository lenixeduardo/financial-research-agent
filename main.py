from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from app.config import settings
from app.errors import AssetNotFoundError, ProviderTimeoutError
from app.schemas import AnalysisResult, AssetRequest
from app.service import FinancialAnalysisService

app = FastAPI(title=settings.app_name, version=settings.app_version)
service = FinancialAnalysisService()


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "version": settings.app_version}


@app.post("/analyses", response_model=AnalysisResult)
async def create_analysis(payload: AssetRequest) -> AnalysisResult:
    return await service.analyze(payload.ticker)


@app.exception_handler(AssetNotFoundError)
async def asset_not_found_handler(
    request: Request, exc: AssetNotFoundError
) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={"error": "asset_not_found", "detail": str(exc)},
    )


@app.exception_handler(ProviderTimeoutError)
async def provider_timeout_handler(
    request: Request, exc: ProviderTimeoutError
) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_504_GATEWAY_TIMEOUT,
        content={"error": "provider_timeout", "detail": str(exc)},
    )

