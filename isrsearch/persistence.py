"""Track persistence: how uncertainty grows after contact is lost, and what
it costs to get the target back.

The radius of possible positions grows linearly with the gap; the area to
re-search grows with its square. Doubling a gap quadruples the re-search.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

__all__ = [
    "uncertainty_radius",
    "uncertainty_area",
    "reacquisition_time",
    "max_affordable_gap",
    "Reacquisition",
    "reacquire",
]


def uncertainty_radius(target_speed_kt: float, gap_h: float) -> float:
    """r = v_max * t_gap (NM). A worst-case bound for a target that may turn."""
    if target_speed_kt < 0 or gap_h < 0:
        raise ValueError("speed and gap must be non-negative")
    return target_speed_kt * gap_h


def uncertainty_area(target_speed_kt: float, gap_h: float) -> float:
    """A_u = pi r^2 (NM^2)."""
    return math.pi * uncertainty_radius(target_speed_kt, gap_h) ** 2


def reacquisition_time(
    target_pod: float,
    target_speed_kt: float,
    gap_h: float,
    sweep_width_nm: float,
    searcher_speed_kt: float,
) -> float:
    """Hours to re-search the uncertainty area to ``target_pod`` under random
    search: t = -ln(1 - POD) A_u / (W v_g).

    Ignores that the area keeps growing while the re-search runs, so it is
    optimistic for long re-searches.
    """
    if not 0 < target_pod < 1:
        raise ValueError("target_pod must lie in (0, 1)")
    if sweep_width_nm <= 0 or searcher_speed_kt <= 0:
        raise ValueError("sweep width and searcher speed must be positive")
    area = uncertainty_area(target_speed_kt, gap_h)
    return -math.log(1.0 - target_pod) * area / (sweep_width_nm * searcher_speed_kt)


def max_affordable_gap(
    time_budget_h: float,
    target_pod: float,
    target_speed_kt: float,
    sweep_width_nm: float,
    searcher_speed_kt: float,
) -> float:
    """Longest contact gap (h) that can still be recovered to ``target_pod``
    within ``time_budget_h`` of re-search. Inverse of :func:`reacquisition_time`."""
    if time_budget_h < 0:
        raise ValueError("time budget must be non-negative")
    if not 0 < target_pod < 1 or target_speed_kt <= 0:
        raise ValueError("target_pod must lie in (0, 1) and target speed must be positive")
    area = time_budget_h * sweep_width_nm * searcher_speed_kt / -math.log(1.0 - target_pod)
    return math.sqrt(area / math.pi) / target_speed_kt


@dataclass(frozen=True)
class Reacquisition:
    gap_h: float
    radius_nm: float
    area_nm2: float
    hours: float

    def as_text(self) -> str:
        return (
            f"gap {self.gap_h * 60:.0f} min -> radius {self.radius_nm:.1f} NM, "
            f"area {self.area_nm2:,.1f} NM^2, re-search {self.hours:.2f} h"
        )


def reacquire(target_pod, target_speed_kt, gap_h, sweep_width_nm, searcher_speed_kt) -> Reacquisition:
    return Reacquisition(
        gap_h=gap_h,
        radius_nm=uncertainty_radius(target_speed_kt, gap_h),
        area_nm2=uncertainty_area(target_speed_kt, gap_h),
        hours=reacquisition_time(target_pod, target_speed_kt, gap_h, sweep_width_nm, searcher_speed_kt),
    )
