from app.schemas import FinancialMetric, FinancialSnapshot, MetricStatus


def safe_divide(numerator: float, denominator: float) -> float | None:
    return None if denominator == 0 else numerator / denominator


def calculate_metrics(snapshot: FinancialSnapshot) -> list[FinancialMetric]:
    revenue_growth = safe_divide(
        snapshot.revenue - snapshot.previous_revenue, snapshot.previous_revenue
    )
    net_margin = safe_divide(snapshot.net_income, snapshot.revenue)
    debt_to_equity = safe_divide(snapshot.total_debt, snapshot.equity)
    roe = safe_divide(snapshot.net_income, snapshot.equity)
    price_to_earnings = safe_divide(snapshot.market_price, snapshot.earnings_per_share)

    return [
        FinancialMetric(
            name="revenue_growth",
            value=revenue_growth,
            unit="ratio",
            interpretation="Crescimento da receita em relação ao período anterior.",
            status=_growth_status(revenue_growth),
        ),
        FinancialMetric(
            name="net_margin",
            value=net_margin,
            unit="ratio",
            interpretation="Parcela da receita convertida em lucro líquido.",
            status=_threshold_status(net_margin, positive=0.15, negative=0.05),
        ),
        FinancialMetric(
            name="debt_to_equity",
            value=debt_to_equity,
            unit="ratio",
            interpretation="Dívida total em relação ao patrimônio líquido.",
            status=_inverse_threshold_status(debt_to_equity, positive=0.6, negative=1.5),
        ),
        FinancialMetric(
            name="roe",
            value=roe,
            unit="ratio",
            interpretation="Retorno do lucro sobre o patrimônio líquido.",
            status=_threshold_status(roe, positive=0.15, negative=0.05),
        ),
        FinancialMetric(
            name="price_to_earnings",
            value=price_to_earnings,
            unit="multiple",
            interpretation="Preço dividido pelo lucro por ação; exige comparação setorial.",
            status=MetricStatus.NEUTRAL if price_to_earnings is not None else MetricStatus.UNKNOWN,
        ),
    ]


def _growth_status(value: float | None) -> MetricStatus:
    if value is None:
        return MetricStatus.UNKNOWN
    if value > 0.03:
        return MetricStatus.POSITIVE
    if value < 0:
        return MetricStatus.NEGATIVE
    return MetricStatus.NEUTRAL


def _threshold_status(
    value: float | None, *, positive: float, negative: float
) -> MetricStatus:
    if value is None:
        return MetricStatus.UNKNOWN
    if value >= positive:
        return MetricStatus.POSITIVE
    if value < negative:
        return MetricStatus.NEGATIVE
    return MetricStatus.NEUTRAL


def _inverse_threshold_status(
    value: float | None, *, positive: float, negative: float
) -> MetricStatus:
    if value is None:
        return MetricStatus.UNKNOWN
    if value <= positive:
        return MetricStatus.POSITIVE
    if value > negative:
        return MetricStatus.NEGATIVE
    return MetricStatus.NEUTRAL

