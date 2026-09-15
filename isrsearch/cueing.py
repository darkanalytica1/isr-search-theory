"""Cross-cueing: how long a narrow sensor takes to acquire a cued candidate.

This is a first-order model by the author, built from the same random-search
law: slew, settle, then search the cue's error circle with the cued sensor's
footprint. It shows which term dominates; it is not a gimbal performance model.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

__all__ = ["cue_error_radius", "CueTime", "cue_time"]


def cue_error_radius(position_error_m: float, cue_age_s: float, target_speed_m_s: float) -> float:
    """Worst-case error radius when the cued sensor arrives: the cue's own
    position error plus the distance the target could travel while the cue aged."""
    if min(position_error_m, cue_age_s, target_speed_m_s) < 0:
        raise ValueError("inputs must be non-negative")
    return position_error_m + target_speed_m_s * cue_age_s


@dataclass(frozen=True)
class CueTime:
    slew_s: float
    settle_s: float
    search_s: float

    @property
    def total_s(self) -> float:
        return self.slew_s + self.settle_s + self.search_s

    @property
    def dominant(self) -> str:
        parts = {"slew": self.slew_s, "settle": self.settle_s, "search": self.search_s}
        return max(parts, key=parts.get)

    def as_text(self) -> str:
        return (
            f"slew {self.slew_s:.1f} s + settle {self.settle_s:.1f} s + search {self.search_s:.1f} s "
            f"= {self.total_s:.1f} s (dominant: {self.dominant})"
        )


def cue_time(
    error_radius_m: float,
    footprint_width_m: float,
    scan_speed_m_s: float,
    slew_deg: float = 0.0,
    slew_rate_deg_s: float = 30.0,
    settle_s: float = 0.0,
    target_pod: float = 0.9,
) -> CueTime:
    """Slew + settle + search of the error circle.

    If the footprint already covers the error circle (width >= diameter) the
    search term is zero: one look is enough. Otherwise the footprint sweeps the
    circle at area rate ``footprint_width_m * scan_speed_m_s`` under the
    random-search law.
    """
    if footprint_width_m <= 0 or slew_rate_deg_s <= 0:
        raise ValueError("footprint width and slew rate must be positive")
    if not 0 < target_pod < 1:
        raise ValueError("target_pod must lie in (0, 1)")
    if min(error_radius_m, slew_deg, settle_s) < 0:
        raise ValueError("inputs must be non-negative")
    slew = slew_deg / slew_rate_deg_s
    if footprint_width_m >= 2.0 * error_radius_m:
        search = 0.0
    else:
        if scan_speed_m_s <= 0:
            raise ValueError("scan speed must be positive when the footprint is smaller than the error circle")
        area = math.pi * error_radius_m**2
        search = -math.log(1.0 - target_pod) * area / (footprint_width_m * scan_speed_m_s)
    return CueTime(slew, settle_s, search)
