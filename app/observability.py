from collections import deque
from datetime import UTC, datetime
from time import perf_counter
from uuid import uuid4

from app.schemas import AnalysisTrace, ObservabilitySummary, RunStatus, ToolCallTrace


class InMemoryTraceStore:
    """Bounded local trace store for development and demonstrable observability."""

    def __init__(self, max_runs: int = 200) -> None:
        self._runs: deque[AnalysisTrace] = deque(maxlen=max_runs)

    def save(self, trace: AnalysisTrace) -> None:
        self._runs.append(trace)

    def list(self) -> list[AnalysisTrace]:
        return list(reversed(self._runs))

    def summary(self) -> ObservabilitySummary:
        runs = list(self._runs)
        total = len(runs)
        answered = sum(run.status == RunStatus.ANSWERED for run in runs)
        insufficient = sum(run.status == RunStatus.INSUFFICIENT_DATA for run in runs)
        tool_errors = sum(run.status == RunStatus.TOOL_ERROR for run in runs)
        completed_latencies = [run.latency_ms for run in runs if run.latency_ms is not None]
        average_latency = (
            sum(completed_latencies) / len(completed_latencies)
            if completed_latencies
            else None
        )
        return ObservabilitySummary(
            total_runs=total,
            answered_runs=answered,
            insufficient_data_runs=insufficient,
            tool_error_runs=tool_errors,
            answer_rate=answered / total if total else 0,
            average_latency_ms=average_latency,
        )


def start_trace(ticker: str) -> tuple[AnalysisTrace, float]:
    return (
        AnalysisTrace(
            run_id=str(uuid4()),
            ticker=ticker,
            started_at=datetime.now(UTC),
        ),
        perf_counter(),
    )


def add_tool_call(
    trace: AnalysisTrace,
    *,
    name: str,
    arguments: dict[str, str],
    started_at: float,
    error: Exception | None = None,
) -> None:
    trace.tool_calls.append(
        ToolCallTrace(
            name=name,
            arguments=arguments,
            status="error" if error else "success",
            duration_ms=round((perf_counter() - started_at) * 1000),
            error=str(error) if error else None,
        )
    )


def finish_trace(
    trace: AnalysisTrace,
    *,
    started_at: float,
    status: RunStatus,
    sources: list[str] | None = None,
    error: Exception | None = None,
) -> None:
    trace.completed_at = datetime.now(UTC)
    trace.status = status
    trace.latency_ms = round((perf_counter() - started_at) * 1000)
    trace.sources = sources or []
    trace.citations_count = len(trace.sources)
    trace.error = str(error) if error else None
