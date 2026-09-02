from app.metrics import calculate_metrics, safe_divide
from app.schemas import FinancialSnapshot, MetricStatus


def snapshot(**overrides: float) -> FinancialSnapshot:
    values = {
        "revenue": 120.0,
        "previous_revenue": 100.0,
        "net_income": 24.0,
        "equity": 80.0,
        "total_debt": 40.0,
        "market_price": 30.0,
        "earnings_per_share": 3.0,
    }
    values.update(overrides)
    return FinancialSnapshot(**values)


def test_safe_divide_handles_zero() -> None:
    assert safe_divide(10, 0) is None


def test_calculates_five_metrics() -> None:
    metrics = calculate_metrics(snapshot())
    assert len(metrics) == 5
    assert {item.name for item in metrics} == {
        "revenue_growth",
        "net_margin",
        "debt_to_equity",
        "roe",
        "price_to_earnings",
    }


def test_growth_is_positive() -> None:
    metric = calculate_metrics(snapshot())[0]
    assert metric.value == 0.2
    assert metric.status == MetricStatus.POSITIVE


def test_declining_revenue_is_negative() -> None:
    metric = calculate_metrics(snapshot(revenue=90.0))[0]
    assert metric.status == MetricStatus.NEGATIVE


def test_missing_pe_becomes_unknown() -> None:
    metric = calculate_metrics(snapshot(earnings_per_share=0.0))[-1]
    assert metric.value is None
    assert metric.status == MetricStatus.UNKNOWN

