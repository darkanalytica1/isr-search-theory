"""isrsearch: search theory for wide-area ISR planning. Pure standard library;
matplotlib is optional and used only for plotting."""

from .burden import AlertBurden, alert_burden, sensor_value
from .cueing import CueTime, cue_error_radius, cue_time
from .persistence import (
    Reacquisition,
    max_affordable_gap,
    reacquire,
    reacquisition_time,
    uncertainty_area,
    uncertainty_radius,
)
from .search import (
    M_PER_NM,
    POD_MODELS,
    SearchPlan,
    coverage_factor,
    coverage_rate,
    footprint_width,
    pod,
    pod_curve,
    pod_exhaustive,
    pod_parallel,
    pod_random,
    time_required,
    track_length_required,
)

__version__ = "0.1.0"

__all__ = [
    "AlertBurden", "CueTime", "M_PER_NM", "POD_MODELS", "Reacquisition", "SearchPlan",
    "alert_burden", "coverage_factor", "coverage_rate", "cue_error_radius", "cue_time",
    "footprint_width", "max_affordable_gap", "pod", "pod_curve", "pod_exhaustive",
    "pod_parallel", "pod_random", "reacquire", "reacquisition_time", "sensor_value",
    "time_required", "track_length_required", "uncertainty_area", "uncertainty_radius",
]
