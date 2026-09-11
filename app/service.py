from time import perf_counter

from app.config import settings
from app.metrics import calculate_metrics
from app.observability import add_agent_step, add_model_usage, add_tool_call
from app.providers import FinancialDataProvider, build_financial_provider
from app.schemas import (
    AnalysisResult,
    AnalysisTrace,
    MetricStatus,
    RiskSeverity,
    RiskSignal,
)
from app.verifier import verify_analysis


class FinancialAnalysisService:
    def __init__(self, provider: FinancialDataProvider | None = None) -> None:
        self.provider = provider or build_financial_provider()

    async def analyze(self, ticker: str, trace: AnalysisTrace) -> AnalysisResult:
        research_started_at = perf_counter()
        tool_started_at = perf_counter()
        try:
            profile, snapshot, source = await self.provider.get_asset(ticker)
        except Exception as exc:
            add_tool_call(
                trace,
                name="get_asset",
                arguments={"ticker": ticker},
                started_at=tool_started_at,
                error=exc,
            )
            add_agent_step(
                trace,
                name="research_agent",
                started_at=research_started_at,
                status="error",
                details={"ticker": ticker},
            )
            raise
        add_tool_call(
            trace,
            name="get_asset",
            arguments={"ticker": ticker},
            started_at=tool_started_at,
        )
        add_agent_step(
            trace,
            name="research_agent",
            started_at=research_started_at,
            details={"provider": source.provider, "is_mock": source.is_mock},
        )

        analysis_started_at = perf_counter()
        metrics = calculate_metrics(snapshot)
        negatives = [metric for metric in metrics if metric.status == MetricStatus.NEGATIVE]
        positives = [metric for metric in metrics if metric.status == MetricStatus.POSITIVE]

        risks = [
            RiskSignal(
                category=metric.name,
                description=f"O indicador {metric.name} exige atenção.",
                severity=RiskSeverity.MEDIUM,
                evidence=f"Valor calculado: {metric.value:.4f}",
            )
            for metric in negatives
            if metric.value is not None
        ]

        summary = (
            f"{profile.company_name} possui {len(positives)} indicador(es) positivo(s), "
            f"{len(negatives)} negativo(s) e os demais neutros ou indisponíveis."
        )
        known_metrics = sum(metric.value is not None for metric in metrics)
        confidence = 0.9 if known_metrics == len(metrics) else max(0.45, known_metrics / len(metrics))

        result = AnalysisResult(
            ticker=profile.ticker,
            company_name=profile.company_name,
            summary=summary,
            metrics=metrics,
            risks=risks,
            positive_signals=[metric.interpretation for metric in positives],
            missing_information=[
                metric.name for metric in metrics if metric.value is None
            ],
            sources=[source],
            confidence=confidence,
        )
        add_agent_step(
            trace,
            name="financial_analysis_agent",
            started_at=analysis_started_at,
            details={"metrics": len(metrics), "risks": len(risks), "confidence": confidence},
        )

        verifier_started_at = perf_counter()
        result.verification = verify_analysis(result)
        add_agent_step(
            trace,
            name="verifier",
            started_at=verifier_started_at,
            status="success" if result.verification.passed else "warning",
            details={
                "checks": len(result.verification.checks),
                "warnings": len(result.verification.warnings),
            },
        )

        # The current pipeline is deterministic; this field is already wired for future LLM stages.
        add_model_usage(trace, model=settings.default_model, input_tokens=0, output_tokens=0)
        return result
