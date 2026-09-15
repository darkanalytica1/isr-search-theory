"""Operator false-alarm burden and a comparative sensor value model.

A search layer is only as good as the alert queue it creates. Review time
scales with total alerts, not with real ones.
"""

from __future__ import annotations

from dataclasses import dataclass

__all__ = ["AlertBurden", "alert_burden", "sensor_value"]


@dataclass(frozen=True)
class AlertBurden:
    false_alerts: float
    true_alerts: float
    ppv: float
    review_s_per_hour: float

    @property
    def review_min_per_hour(self) -> float:
        return self.review_s_per_hour / 60.0

    @property
    def attention_share(self) -> float:
        """Fraction of one operator-hour spent reviewing alerts (may exceed 1)."""
        return self.review_s_per_hour / 3600.0

    def as_text(self) -> str:
        return "\n".join(
            [
                f"false alerts per hour   {self.false_alerts:,.1f}",
                f"true alerts per hour    {self.true_alerts:,.2f}",
                f"PPV                     {self.ppv:.3f}",
                f"review time per hour    {self.review_s_per_hour:,.0f} s "
                f"({self.review_min_per_hour:.1f} min, {self.attention_share:.0%} of an operator)",
            ]
        )


def alert_burden(
    candidates_per_hour: float,
    pfa: float,
    targets_per_hour: float,
    pd: float,
    review_s: float,
) -> AlertBurden:
    """N_FA = N_c Pfa, N_TP = N_t Pd, PPV = N_TP / (N_TP + N_FA),
    T_review = (N_TP + N_FA) t_r."""
    for name, v in (("pfa", pfa), ("pd", pd)):
        if not 0 <= v <= 1:
            raise ValueError(f"{name} must lie in [0, 1]")
    if min(candidates_per_hour, targets_per_hour, review_s) < 0:
        raise ValueError("counts and review time must be non-negative")
    fa = candidates_per_hour * pfa
    tp = targets_per_hour * pd
    total = fa + tp
    return AlertBurden(fa, tp, tp / total if total else float("nan"), total * review_s)


def sensor_value(area_rate: float, pd: float, q_id: float, operator_burden: float) -> float:
    """V = A_dot * Pd * Q_ID / B.

    An analytical comparison aid in arbitrary units, not a published metric.
    Use it only to rank architectures under identical assumptions.
    """
    if operator_burden <= 0:
        raise ValueError("operator_burden must be positive")
    if not (0 <= pd <= 1 and 0 <= q_id <= 1):
        raise ValueError("pd and q_id must lie in [0, 1]")
    return area_rate * pd * q_id / operator_burden
