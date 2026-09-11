"""Run the versioned evaluation suite against the local FastAPI application."""

import json
import sys
from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app

ROOT = Path(__file__).resolve().parents[1]
CASES_PATH = ROOT / "evals" / "cases.json"
REPORT_PATH = ROOT / "evals" / "latest-report.json"


def evaluate() -> dict[str, object]:
    suite = json.loads(CASES_PATH.read_text())
    client = TestClient(app)
    cases: list[dict[str, object]] = []

    for case in suite["cases"]:
        response = client.post("/analyses", json=case["payload"])
        expected = case["expected"]
        checks: dict[str, bool] = {"http_status": response.status_code == expected["http_status"]}
        body = response.json()
        if "ticker" in expected:
            checks["ticker"] = body.get("ticker") == expected["ticker"]
        if "error" in expected:
            checks["error"] = body.get("error") == expected["error"]
        if response.status_code == 200:
            checks["verification_present"] = body.get("verification") is not None
            checks["source_provenance"] = bool(body.get("sources"))
            checks["confidence_bounded"] = 0 <= body.get("confidence", -1) <= 1

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
                if response.status_code == 200:
                    checks["agent_steps"] = len(trace.get("agent_steps", [])) >= 3
                    checks["model_routing"] = len(trace.get("model_usage", [])) >= 2
        cases.append({"id": case["id"], "passed": all(checks.values()), "checks": checks})

    passed = sum(bool(item["passed"]) for item in cases)
    total = len(cases)
    report = {
        "suite": suite.get("name", "financial-research-agent-baseline"),
        "passed": passed,
        "total": total,
        "pass_rate": passed / total if total else 0,
        "cases": cases,
    }
    REPORT_PATH.write_text(json.dumps(report, indent=2, ensure_ascii=False))
    return report


if __name__ == "__main__":
    result = evaluate()
    print(json.dumps(result, indent=2, ensure_ascii=False))
    sys.exit(0 if result["pass_rate"] == 1.0 else 1)
