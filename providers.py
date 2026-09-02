import asyncio

from app.errors import AssetNotFoundError, ProviderTimeoutError
from app.schemas import CompanyProfile, DataSource, FinancialSnapshot


class MockFinancialDataProvider:
    """Deterministic provider for local development and tests."""

    _assets = {
        "PETR4": (
            CompanyProfile(
                ticker="PETR4",
                company_name="Petróleo Brasileiro S.A.",
                sector="Energy",
            ),
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
            CompanyProfile(
                ticker="VALE3",
                company_name="Vale S.A.",
                sector="Basic Materials",
            ),
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

