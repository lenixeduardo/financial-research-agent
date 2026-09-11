from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_analysis_exposes_verification_and_agent_trace() -> None:
    response = client.post("/analyses", json={"ticker": "PETR4"})
    assert response.status_code == 200
    body = response.json()
    assert body["verification"]["passed"] is True
    assert "source_provenance_present" in body["verification"]["checks"]

    run_id = response.headers["X-Run-ID"]
    runs = client.get("/observability/runs").json()
    trace = next(item for item in runs if item["run_id"] == run_id)
    assert [step["name"] for step in trace["agent_steps"]] == [
        "research_agent",
        "financial_analysis_agent",
        "verifier",
    ]
    assert trace["model_usage"][0]["model"]
    assert trace["estimated_cost_usd"] >= 0


def test_observability_summary_exposes_unit_economics() -> None:
    client.post("/analyses", json={"ticker": "VALE3"})
    summary = client.get("/observability/summary")
    assert summary.status_code == 200
    body = summary.json()
    assert "total_estimated_cost_usd" in body
    assert "average_cost_per_answered_run_usd" in body
