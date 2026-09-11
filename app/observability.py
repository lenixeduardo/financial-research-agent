from collections import deque
from datetime import UTC, datetime
from time import perf_counter
from uuid import uuid4

from app.costs import TokenUsage, estimate_cost_usd
from app.schemas import (
    AgentStepTrace,
    AnalysisTrace,
    ModelUsageTrace,
    ObservabilitySummary,
    RunStatus,
    ToolCallTrace,
)


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
        total_cost = round(sum(run.estimated_cost_usd for run in runs), 8)
        answered_costs = [run.estimated_cost_usd for run in runs if run.status == RunStatus.ANSWERED]
        average_latency = (
            sum(completed_latencies) / len(completed_latencies) if completed_latencies else None
        )
        average_answer_cost = (
            round(sum(answered_costs) / len(answered_costs), 8) if answered_costs else None
        )
        return ObservabilitySummary(
            total_runs=total,
            answered_runs=answered,
            insufficient_data_runs=insufficient,
            tool_error_runs=tool_errors,
            answer_rate=answered / total if total else 0,
            average_latency_ms=average_latency,
            total_estimated_cost_usd=total_cost,
            average_cost_per_answered_run_usd=average_answer_cost,
        )


def start_trace(ticker: str) -> tuple[AnalysisTrace, float]:
    return (
        AnalysisTrace(run_id=str(uuid4()), ticker=ticker, started_at=datetime.now(UTC)),
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


def add_agent_step(
    trace: AnalysisTrace,
    *,
    name: str,
    started_at: float,
    status: str = "success",
    details: dict[str, str | int | float | bool] | None = None,
) -> None:
    trace.agent_steps.append(
        AgentStepTrace(
            name=name,
            status=status,
            duration_ms=round((perf_counter() - started_at) * 1000),
            details=details or {},
        )
    )


def add_model_usage(
    trace: AnalysisTrace,
    *,
    model: str,
    input_tokens: int = 0,
    output_tokens: int = 0,
) -> None:
    usage = TokenUsage(input_tokens=input_tokens, output_tokens=output_tokens)
    cost = estimate_cost_usd(usage)
    trace.model_usage.append(
        ModelUsageTrace(
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            estimated_cost_usd=cost,
        )
    )
    trace.estimated_cost_usd = round(trace.estimated_cost_usd + cost, 8)


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
