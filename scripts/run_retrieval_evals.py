"""Evaluate retrieval quality with a small versioned benchmark."""

import json
import sys
from pathlib import Path

from app.retrieval import hybrid_rank

ROOT = Path(__file__).resolve().parents[1]
CASES_PATH = ROOT / "evals" / "retrieval_cases.json"


def evaluate() -> dict[str, object]:
    suite = json.loads(CASES_PATH.read_text())
    corpus = [(item["id"], item["text"]) for item in suite["corpus"]]
    reciprocal_ranks: list[float] = []
    recall_at_1 = 0
    details = []

    for case in suite["cases"]:
        ranked = hybrid_rank(case["query"], corpus, top_k=5, min_score=0.0)
        ids = [item.key for item in ranked]
        relevant = case["relevant_id"]
        rank = ids.index(relevant) + 1 if relevant in ids else None
        if rank == 1:
            recall_at_1 += 1
        reciprocal_ranks.append(1 / rank if rank else 0.0)
        details.append({"query": case["query"], "relevant_id": relevant, "rank": rank, "top": ids[:3]})

    total = len(suite["cases"])
    metrics = {
        "recall_at_1": recall_at_1 / total if total else 0.0,
        "mrr": sum(reciprocal_ranks) / total if total else 0.0,
    }
    return {"suite": suite["name"], "metrics": metrics, "cases": details}


if __name__ == "__main__":
    report = evaluate()
    print(json.dumps(report, indent=2, ensure_ascii=False))
    metrics = report["metrics"]
    sys.exit(0 if metrics["recall_at_1"] >= 0.75 and metrics["mrr"] >= 0.85 else 1)
