"""Search theory: sweep width, coverage and probability of detection.

Units follow maritime search practice: nautical miles (NM), knots (kt),
hours (h). Any consistent unit system works if you are consistent.

The effective sweep width W is not a sensor property. It is defined for a
stated sensor, target, altitude and environment, and it is the assumption
every number below depends on.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Iterable

__all__ = [
    "M_PER_NM",
    "coverage_rate",
    "footprint_width",
    "coverage_factor",
    "pod_random",
    "pod_parallel",
    "pod_exhaustive",
    "POD_MODELS",
    "pod",
    "track_length_required",
    "time_required",
    "SearchPlan",
    "pod_curve",
]

M_PER_NM = 1852.0


def _positive(name: str, value: float) -> None:
    if value <= 0:
        raise ValueError(f"{name} must be positive, got {value!r}")


def coverage_rate(sweep_width_nm: float, speed_kt: float) -> float:
    """Area searched per hour, A_dot = W * v (NM^2/h)."""
    _positive("sweep_width_nm", sweep_width_nm)
    _positive("speed_kt", speed_kt)
    return sweep_width_nm * speed_kt


def footprint_width(slant_range_m: float, fov_deg: float) -> float:
    """Ground footprint width of a staring sensor, w = 2 R tan(FOV / 2), in metres.

    >>> round(footprint_width(5000, 2))
    175
    """
    _positive("slant_range_m", slant_range_m)
    if not 0 < fov_deg < 180:
        raise ValueError("fov_deg must lie in (0, 180)")
    return 2.0 * slant_range_m * math.tan(math.radians(fov_deg) / 2.0)


def coverage_factor(sweep_width_nm: float, track_length_nm: float, area_nm2: float) -> float:
    """C = W * L / A: swept area divided by search area."""
    _positive("sweep_width_nm", sweep_width_nm)
    _positive("area_nm2", area_nm2)
    if track_length_nm < 0:
        raise ValueError("track_length_nm must be non-negative")
    return sweep_width_nm * track_length_nm / area_nm2


def pod_random(c: float) -> float:
    """Koopman random-search law, POD = 1 - exp(-C). The conservative
    planning curve: the track covers the area as if at random, with overlap.

    >>> round(pod_random(0.64), 2)
    0.47
    """
    if c < 0:
        raise ValueError("coverage factor must be non-negative")
    return 1.0 - math.exp(-c)


def pod_parallel(c: float) -> float:
    """Parallel sweep under an inverse-cube detection law,
    POD = erf(sqrt(pi) / 2 * C). An upper-end curve for well-flown sweeps."""
    if c < 0:
        raise ValueError("coverage factor must be non-negative")
    return math.erf(math.sqrt(math.pi) / 2.0 * c)


def pod_exhaustive(c: float) -> float:
    """Exhaustive search with a definite-range sensor and perfect lane spacing,
    POD = min(1, C). An idealised ceiling that no real search reaches."""
    if c < 0:
        raise ValueError("coverage factor must be non-negative")
    return min(1.0, c)


POD_MODELS = {"random": pod_random, "parallel": pod_parallel, "exhaustive": pod_exhaustive}


def pod(c: float, model: str = "random") -> float:
    try:
        return POD_MODELS[model](c)
    except KeyError:
        raise ValueError(f"unknown model {model!r}; choose from {sorted(POD_MODELS)}") from None


def track_length_required(target_pod: float, area_nm2: float, sweep_width_nm: float) -> float:
    """Track length for a target POD under random search, L = -ln(1 - POD) A / W."""
    if not 0 < target_pod < 1:
        raise ValueError("target_pod must lie in (0, 1)")
    _positive("area_nm2", area_nm2)
    _positive("sweep_width_nm", sweep_width_nm)
    return -math.log(1.0 - target_pod) * area_nm2 / sweep_width_nm


def time_required(target_pod: float, area_nm2: float, area_rate_nm2_h: float) -> float:
    """Hours on task for a target POD under random search, given an area rate W*v."""
    if not 0 < target_pod < 1:
        raise ValueError("target_pod must lie in (0, 1)")
    _positive("area_nm2", area_nm2)
    _positive("area_rate_nm2_h", area_rate_nm2_h)
    return -math.log(1.0 - target_pod) * area_nm2 / area_rate_nm2_h


@dataclass(frozen=True)
class SearchPlan:
    """One searcher, one box, one sweep width."""

    area_nm2: float
    sweep_width_nm: float
    speed_kt: float

    def __post_init__(self) -> None:
        _positive("area_nm2", self.area_nm2)
        _positive("sweep_width_nm", self.sweep_width_nm)
        _positive("speed_kt", self.speed_kt)

    @property
    def area_rate(self) -> float:
        return coverage_rate(self.sweep_width_nm, self.speed_kt)

    def coverage(self, hours: float) -> float:
        return coverage_factor(self.sweep_width_nm, self.speed_kt * hours, self.area_nm2)

    def pod(self, hours: float, model: str = "random") -> float:
        return pod(self.coverage(hours), model)

    def hours_for(self, target_pod: float) -> float:
        return time_required(target_pod, self.area_nm2, self.area_rate)

    def as_text(self, hours: float) -> str:
        c = self.coverage(hours)
        return "\n".join(
            [
                f"area              {self.area_nm2:,.0f} NM^2",
                f"sweep width       {self.sweep_width_nm:g} NM (assumed for target and conditions)",
                f"speed             {self.speed_kt:g} kt  ->  {self.area_rate:,.0f} NM^2/h",
                f"time on task      {hours:g} h  ->  track {self.speed_kt * hours:,.0f} NM",
                f"coverage factor   C = {c:.2f}",
                f"POD random        {pod_random(c):.2f}",
                f"POD parallel      {pod_parallel(c):.2f}",
                f"hours for POD 0.9 (random)  {self.hours_for(0.9):.1f}",
            ]
        )


def pod_curve(plan: SearchPlan, hours: Iterable[float], models: Iterable[str] = ("random", "parallel")):
    """Rows of (hours, POD per model) for plotting or CSV export."""
    models = tuple(models)
    return [(h, *(plan.pod(h, m) for m in models)) for h in hours]
