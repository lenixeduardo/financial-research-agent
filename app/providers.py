import asyncio
from typing import Protocol

import httpx

from app.config import settings
from app.errors import AssetNotFoundError, ProviderTimeoutError
from app.schemas import CompanyProfile, DataSource, FinancialSnapshot


class FinancialDataProvider(Protocol):
    async def get_asset(
        self, ticker: str
    ) -> tuple[CompanyProfile, FinancialSnapshot, DataSource]: ...


class BrapiFinancialDataProvider:
    """Production-oriented BRAPI adapter with explicit source provenance."""

    async def get_asset(
        self, ticker: str
    ) -> tuple[CompanyProfile, FinancialSnapshot, DataSource]:
        params = {"symbols": ticker}
        if settings.brapi_token:
            params["token"] = settings.brapi_token
        url = f"{settings.brapi_base_url.rstrip('/')}/v2/stocks/quote"
        try:
            async with httpx.AsyncClient(timeout=settings.provider_timeout_seconds) as client:
                response = await client.get(url, params=params)
                response.raise_for_status()
        except httpx.TimeoutException as exc:
            raise ProviderTimeoutError("BRAPI request timed out") from exc
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code == 404:
                raise AssetNotFoundError(f"asset {ticker} was not found") from exc
            raise ProviderTimeoutError(
                f"BRAPI returned HTTP {exc.response.status_code}"
            ) from exc

        payload = response.json()
        results = payload.get("results") or []
        if not results:
            raise AssetNotFoundError(f"asset {ticker} was not found")
        raw = results[0]
        data = raw.get("data") if isinstance(raw.get("data"), dict) else raw

        def number(*keys: str, default: float = 0.0) -> float:
            for key in keys:
                value = data.get(key)
                if isinstance(value, (int, float)):
                    return float(value)
            return default

        profile = CompanyProfile(
            ticker=str(data.get("symbol") or ticker).upper(),
            company_name=str(data.get("longName") or data.get("shortName") or ticker),
            currency=str(data.get("currency") or "BRL"),
            sector=str(data.get("sector") or "Unknown"),
        )
        snapshot = FinancialSnapshot(
            revenue=number("totalRevenue", "revenue"),
            previous_revenue=number("previousRevenue", "revenuePreviousYear"),
            net_income=number("netIncome", "netIncomeToCommon"),
            equity=number("totalStockholderEquity", "equity"),
            total_debt=number("totalDebt"),
            market_price=number("regularMarketPrice", "price"),
            earnings_per_share=number("earningsPerShare", "epsTrailingTwelveMonths", "eps"),
        )
        source = DataSource(
            provider="brapi",
            reference=str(response.url),
            is_mock=False,
        )
        return profile, snapshot, source


class MockFinancialDataProvider:
    """Deterministic provider for local development and tests."""

    _assets = {
        "PETR4": (
            CompanyProfile(ticker="PETR4", company_name="Petróleo Brasileiro S.A.", sector="Energy"),
            FinancialSnapshot(
                revenue=490_000_000_000,
                previous_revenue=475_000_000_000,
                net_income=82_000_000_000,
                equity=390_000_000_000,
                total_debt=280_000_000_000,
                market_price=38.0,
                earnings_per_share=6.0,
            ),
        ),
        "VALE3": (
            CompanyProfile(ticker="VALE3", company_name="Vale S.A.", sector="Basic Materials"),
            FinancialSnapshot(
                revenue=210_000_000_000,
                previous_revenue=230_000_000_000,
                net_income=38_000_000_000,
                equity=205_000_000_000,
                total_debt=88_000_000_000,
                market_price=62.0,
                earnings_per_share=8.1,
            ),
        ),
    }

    async def get_asset(
        self, ticker: str
    ) -> tuple[CompanyProfile, FinancialSnapshot, DataSource]:
        try:
            async with asyncio.timeout(2):
                await asyncio.sleep(0)
                if ticker == "TIMEOUT":
                    raise ProviderTimeoutError("provider request timed out")
                if ticker not in self._assets:
                    raise AssetNotFoundError(f"asset {ticker} was not found")
                profile, snapshot = self._assets[ticker]
                source = DataSource(
                    provider="mock-financial-provider",
                    reference=f"mock://assets/{ticker}",
                )
                return profile, snapshot, source
        except TimeoutError as exc:
            raise ProviderTimeoutError("provider request timed out") from exc


def build_financial_provider() -> FinancialDataProvider:
    if settings.financial_provider.casefold() == "brapi":
        return BrapiFinancialDataProvider()
    return MockFinancialDataProvider()
