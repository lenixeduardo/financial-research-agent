import pytest

from app.errors import ProviderResponseError
from app.providers import BrapiFinancialDataProvider


class _FakeResponse:
    def __init__(self, payload: object = None, *, malformed: bool = False) -> None:
        self.payload = payload
        self.malformed = malformed
        self.url = "https://brapi.dev/api/v2/stocks/quote?symbols=PETR4"

    def raise_for_status(self) -> None:
        return None

    def json(self) -> object:
        if self.malformed:
            raise ValueError("invalid json")
        return self.payload


class _FakeAsyncClient:
    def __init__(self, response: _FakeResponse) -> None:
        self.response = response

    async def __aenter__(self) -> "_FakeAsyncClient":
        return self

    async def __aexit__(self, exc_type: object, exc: object, tb: object) -> None:
        return None

    async def get(self, url: str, params: dict[str, str]) -> _FakeResponse:
        return self.response


@pytest.mark.asyncio
async def test_brapi_missing_fields_remain_none(monkeypatch: pytest.MonkeyPatch) -> None:
    response = _FakeResponse(
        {
            "results": [
                {
                    "symbol": "PETR4",
                    "longName": "Petrobras",
                    "currency": "BRL",
                    "sector": "Energy",
                    "regularMarketPrice": "38.5",
                }
            ]
        }
    )
    monkeypatch.setattr(
        "app.providers.httpx.AsyncClient",
        lambda *args, **kwargs: _FakeAsyncClient(response),
    )

    _, snapshot, _ = await BrapiFinancialDataProvider().get_asset("PETR4")

    assert snapshot.market_price == 38.5
    assert snapshot.revenue is None
    assert snapshot.previous_revenue is None
    assert snapshot.net_income is None
    assert snapshot.equity is None
    assert snapshot.total_debt is None
    assert snapshot.earnings_per_share is None


@pytest.mark.asyncio
async def test_brapi_malformed_json_becomes_provider_response_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    response = _FakeResponse(malformed=True)
    monkeypatch.setattr(
        "app.providers.httpx.AsyncClient",
        lambda *args, **kwargs: _FakeAsyncClient(response),
    )

    with pytest.raises(ProviderResponseError, match="malformed JSON"):
        await BrapiFinancialDataProvider().get_asset("PETR4")
