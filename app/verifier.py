import math

from app.schemas import AnalysisResult, VerificationResult


def verify_analysis(result: AnalysisResult) -> VerificationResult:
    checks: list[str] = []
    warnings: list[str] = []

    if result.sources:
        checks.append("source_provenance_present")
    else:
        warnings.append("analysis_has_no_sources")

    invalid_metrics = [
        metric.name
        for metric in result.metrics
        if metric.value is not None and not math.isfinite(metric.value)
    ]
    if invalid_metrics:
        warnings.append(f"non_finite_metrics:{','.join(invalid_metrics)}")
    else:
        checks.append("financial_metrics_are_finite")

    if result.confidence >= 0.8 and result.missing_information:
        warnings.append("high_confidence_with_known_missing_information")
    else:
        checks.append("confidence_is_consistent_with_missing_information")

    unsupported_risks = [risk.category for risk in result.risks if not risk.evidence.strip()]
    if unsupported_risks:
        warnings.append(f"risk_without_evidence:{','.join(unsupported_risks)}")
    else:
        checks.append("risk_signals_include_evidence")

    return VerificationResult(passed=not warnings, checks=checks, warnings=warnings)
