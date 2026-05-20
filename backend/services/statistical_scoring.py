"""
Continuous statistical helpers for PR analytics (no buckets, no randomness).

Uses sigmoid scaling, percentile ranks, and log-normalized ratios so each PR's
inputs produce a distinct score when underlying metrics differ.
"""
from __future__ import annotations

import math
from typing import Iterable, List, Optional, Sequence


def clamp(value: float, lo: float = 0.0, hi: float = 100.0) -> float:
    return max(lo, min(hi, value))


def sigmoid(x: float, steepness: float = 1.0, midpoint: float = 0.0) -> float:
    """Maps real line to (0, 1)."""
    z = steepness * (x - midpoint)
    z = max(-20.0, min(20.0, z))
    return 1.0 / (1.0 + math.exp(-z))


def log_ratio(value: float, reference: float, floor: float = 1.0) -> float:
    """log1p(value) / log1p(reference) — continuous size vs baseline."""
    ref = max(reference, floor)
    return math.log1p(max(0.0, value)) / math.log1p(ref)


def percentile_rank(value: float, population: Sequence[float]) -> float:
    """
    Fraction of population strictly below value (0–1).
    Uses empirical CDF for repo-relative normalization.
    """
    if not population:
        return 0.5
    sorted_pop = sorted(population)
    n = len(sorted_pop)
    below = sum(1 for v in sorted_pop if v < value)
    equal = sum(1 for v in sorted_pop if v == value)
    return clamp((below + 0.5 * equal) / n, 0.0, 1.0)


def weighted_score(factors: dict[str, float], weights: dict[str, float]) -> float:
    """Weighted average of factors in [0, 1] -> [0, 100]."""
    total_w = sum(weights.values()) or 1.0
    blended = sum(factors.get(k, 0.0) * weights.get(k, 0.0) for k in weights) / total_w
    return round(clamp(blended * 100.0, 0.0, 100.0), 1)


def robust_percentile(values: Sequence[float], p: float) -> float:
    if not values:
        return 0.0
    sorted_values = sorted(values)
    idx = (p / 100.0) * (len(sorted_values) - 1)
    lo = int(math.floor(idx))
    hi = int(math.ceil(idx))
    if lo == hi:
        return float(sorted_values[lo])
    frac = idx - lo
    return sorted_values[lo] * (1 - frac) + sorted_values[hi] * frac


def hours_between(start, end) -> float:
    if start is None or end is None:
        return 0.0
    return max(0.0, (end - start).total_seconds() / 3600.0)


def days_from_hours(hours: float) -> float:
    return round(hours / 24.0, 2)
