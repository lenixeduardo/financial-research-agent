"""Run the versioned baseline evaluations against the local FastAPI application."""

import json
import sys
from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app

ROOT = Path(__file__).resolve().parents[1]
CASES_PATH = ROOT / "evals" / "cases.json"


def evaluate() -> list[dict[str, object]]:
    suite = json.loads(CASES_PATH.read_text())
    client = TestClient(app)
    report: list[dict[str, object]] = []
    for case in suite["cases"]:
        response = client.post("/analyses", json=case["payload"])
        expected = case["expected"]
        checks: dict[str, bool] = {"http_status": response.status_code == expected["http_status"]}
        body = response.json()
        if "ticker" in expected:
            checks["ticker"] = body.get("ticker") == expected["ticker"]
        if "error" in expected:
            checks["error"] = body.get("error") == expected["error"]

        if "trace_status" in expected:
            run_id = response.headers["X-Run-ID"]
            runs = client.get("/observability/runs").json()
            trace = next((item for item in runs if item["run_id"] == run_id), None)
            checks["trace_created"] = trace is not None
            if trace is not None:
                checks["trace_status"] = trace["status"] == expected["trace_status"]
                checks["tool_status"] = trace["tool_calls"][0]["status"] == expected["tool_status"]
                if expected.get("source_required"):
                    checks["source"] = trace["citations_count"] >= 1
        report.append({"id": case["id"], "passed": all(checks.values()), "checks": checks})
    return report


if __name__ == "__main__":
    results = evaluate()
    print(json.dumps(results, indent=2))
    sys.exit(0 if all(item["passed"] for item in results) else 1)
