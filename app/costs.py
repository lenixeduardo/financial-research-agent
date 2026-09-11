from dataclasses import dataclass

from app.config import settings


@dataclass(frozen=True)
class TokenUsage:
    input_tokens: int = 0
    output_tokens: int = 0

    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens


def estimate_cost_usd(usage: TokenUsage) -> float:
    input_cost = (usage.input_tokens / 1_000_000) * settings.input_cost_per_million_tokens_usd
    output_cost = (usage.output_tokens / 1_000_000) * settings.output_cost_per_million_tokens_usd
    return round(input_cost + output_cost, 8)
