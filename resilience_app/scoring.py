from __future__ import annotations

from .models import AnalysisRequest


LOW_MAX = 2.5
MEDIUM_MAX = 4.0


def _to_numeric(value: str) -> int | None:
    if value in {"", "NA", None}:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def compute_profile(scores: dict[str, list[str]]) -> dict[str, str]:
    profile: dict[str, str] = {}

    for factor_key, values in scores.items():
        numeric_values = [
            parsed
            for parsed in (_to_numeric(value) for value in values)
            if parsed is not None
        ]

        if not numeric_values:
            profile[factor_key] = AnalysisRequest.ResilienceLevel.LOW
            continue

        average_score = sum(numeric_values) / len(numeric_values)

        if average_score <= LOW_MAX:
            profile[factor_key] = AnalysisRequest.ResilienceLevel.LOW
        elif average_score <= MEDIUM_MAX:
            profile[factor_key] = AnalysisRequest.ResilienceLevel.MEDIUM
        else:
            profile[factor_key] = AnalysisRequest.ResilienceLevel.HIGH

    return profile