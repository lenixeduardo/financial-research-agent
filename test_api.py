from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_analyze_known_asset() -> None:
    response = client.post("/analyses", json={"ticker": "petr4"})
    assert response.status_code == 200
    body = response.json()
    assert body["ticker"] == "PETR4"
    assert len(body["metrics"]) == 5
    assert body["sources"][0]["is_mock"] is True
    assert "não constitui recomendação" in body["disclaimer"]


def test_unknown_asset_returns_404() -> None:
    response = client.post("/analyses", json={"ticker": "ABCD3"})
    assert response.status_code == 404
    assert response.json()["error"] == "asset_not_found"


def test_invalid_ticker_returns_422() -> None:
    response = client.post("/analyses", json={"ticker": "$$$"})
    assert response.status_code == 422


def test_timeout_returns_504() -> None:
    response = client.post("/analyses", json={"ticker": "TIMEOUT"})
    assert response.status_code == 504
    assert response.json()["error"] == "provider_timeout"

