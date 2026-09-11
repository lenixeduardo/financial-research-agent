from dataclasses import dataclass
from enum import StrEnum

from app.config import settings


class ModelTask(StrEnum):
    EXTRACTION = "extraction"
    RETRIEVAL = "retrieval"
    ANALYSIS = "analysis"
    VERIFICATION = "verification"


@dataclass(frozen=True)
class ModelDecision:
    task: ModelTask
    model: str
    reason: str
    max_cost_usd: float


class ModelRouter:
    """Central model policy.

    The current project keeps deterministic implementations for reproducible tests,
    but routing is explicit so hosted/local LLMs can be swapped per task without
    changing domain services.
    """

    def route(self, task: ModelTask, *, complexity: float = 0.5) -> ModelDecision:
        complexity = min(1.0, max(0.0, complexity))
        if task in {ModelTask.EXTRACTION, ModelTask.RETRIEVAL}:
            return ModelDecision(
                task=task,
                model=settings.fast_model,
                reason="low-latency structured task",
                max_cost_usd=settings.fast_model_budget_usd,
            )
        if task == ModelTask.VERIFICATION:
            return ModelDecision(
                task=task,
                model=settings.verifier_model,
                reason="independent verification path",
                max_cost_usd=settings.verifier_model_budget_usd,
            )
        model = settings.reasoning_model if complexity >= 0.65 else settings.default_model
        return ModelDecision(
            task=task,
            model=model,
            reason="complexity-aware financial analysis",
            max_cost_usd=settings.reasoning_model_budget_usd,
        )


router = ModelRouter()
