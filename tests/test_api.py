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



def test_successful_analysis_creates_trace() -> None:
    response = client.post("/analyses", json={"ticker": "VALE3"})
    assert response.status_code == 200
    run_id = response.headers["X-Run-ID"]

    runs = client.get("/observability/runs")
    assert runs.status_code == 200
    trace = next(item for item in runs.json() if item["run_id"] == run_id)
    assert trace["status"] == "answered"
    assert trace["citations_count"] == 1
    assert trace["tool_calls"][0]["name"] == "get_asset"
    assert trace["tool_calls"][0]["arguments"] == {"ticker": "VALE3"}
    assert trace["tool_calls"][0]["status"] == "success"


def test_not_found_creates_insufficient_data_trace() -> None:
    response = client.post("/analyses", json={"ticker": "ABCD3"})
    assert response.status_code == 404
    run_id = response.headers["X-Run-ID"]

    runs = client.get("/observability/runs")
    trace = next(item for item in runs.json() if item["run_id"] == run_id)
    assert trace["status"] == "insufficient_data"
    assert trace["tool_calls"][0]["status"] == "error"


def test_timeout_creates_tool_error_trace() -> None:
    response = client.post("/analyses", json={"ticker": "TIMEOUT"})
    assert response.status_code == 504
    run_id = response.headers["X-Run-ID"]

    runs = client.get("/observability/runs")
    trace = next(item for item in runs.json() if item["run_id"] == run_id)
    assert trace["status"] == "tool_error"
    assert trace["tool_calls"][0]["status"] == "error"


def test_observability_summary_is_available() -> None:
    response = client.get("/observability/summary")
    assert response.status_code == 200
    body = response.json()
    assert body["total_runs"] >= 3
    assert 0 <= body["answer_rate"] <= 1
