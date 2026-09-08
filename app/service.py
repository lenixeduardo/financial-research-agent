from time import perf_counter

from app.metrics import calculate_metrics
from app.observability import add_tool_call
from app.providers import MockFinancialDataProvider
from app.schemas import (
    AnalysisResult,
    AnalysisTrace,
    MetricStatus,
    RiskSeverity,
    RiskSignal,
)


class FinancialAnalysisService:
    def __init__(self, provider: MockFinancialDataProvider | None = None) -> None:
        self.provider = provider or MockFinancialDataProvider()

    async def analyze(self, ticker: str, trace: AnalysisTrace) -> AnalysisResult:
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
            raise
        add_tool_call(
            trace,
            name="get_asset",
            arguments={"ticker": ticker},
            started_at=tool_started_at,
        )
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
        confidence = 0.9 if all(metric.value is not None for metric in metrics) else 0.65

        return AnalysisResult(
            ticker=profile.ticker,
            company_name=profile.company_name,
            summary=summary,
            metrics=metrics,
            risks=risks,
            positive_signals=[metric.interpretation for metric in positives],
            missing_information=[
                "Fluxo de caixa",
                "Histórico de preços",
                "Comparação com empresas do mesmo setor",
            ],
            sources=[source],
            confidence=confidence,
        )
