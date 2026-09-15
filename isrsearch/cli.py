"""Command line interface: python -m isrsearch <command> ..."""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path
from typing import Sequence

from .burden import alert_burden
from .cueing import cue_error_radius, cue_time
from .persistence import max_affordable_gap, reacquire
from .search import M_PER_NM, SearchPlan, footprint_width


def cmd_plan(args: argparse.Namespace) -> None:
    plan = SearchPlan(args.area, args.sweep_width, args.speed)
    print(plan.as_text(args.hours))
    if args.pod:
        print(f"hours for POD {args.pod:g} (random)  {plan.hours_for(args.pod):.2f}")


def cmd_footprint(args: argparse.Namespace) -> None:
    w = footprint_width(args.range_m, args.fov)
    w_nm = w / M_PER_NM
    print(f"footprint width   {w:,.0f} m ({w_nm:.3f} NM)")
    print(f"staring area rate {w_nm * args.speed:,.1f} NM^2/h at {args.speed:g} kt")


def write_curve(plan: SearchPlan, hours: float, step: float, out: Path, extra_rate: float | None = None) -> list[Path]:
    """Write POD-versus-time as CSV, and as PNG when matplotlib is available."""
    out.parent.mkdir(parents=True, exist_ok=True)
    n = int(round(hours / step))
    times = [i * step for i in range(n + 1)]
    header = ["hours", "pod_random", "pod_parallel"]
    rows = [[t, plan.pod(t, "random"), plan.pod(t, "parallel")] for t in times]
    alt = None
    if extra_rate:
        alt = SearchPlan(plan.area_nm2, extra_rate / plan.speed_kt, plan.speed_kt)
        header.append("pod_random_alt_rate")
        for row, t in zip(rows, times):
            row.append(alt.pod(t, "random"))
    csv_path = out.with_suffix(".csv")
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(header)
        writer.writerows([[f"{v:.4f}" for v in row] for row in rows])
    written = [csv_path]
    try:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        return written
    fig, ax = plt.subplots(figsize=(8, 4.5), dpi=150)
    ax.plot(times, [r[1] for r in rows], color="#1F3A5F", lw=2,
            label=f"random search, W = {plan.sweep_width_nm:g} NM")
    ax.plot(times, [r[2] for r in rows], color="#5B7083", lw=1.75, ls="--", label="parallel sweep")
    if alt is not None:
        ax.plot(times, [r[3] for r in rows], color="#A33A2B", lw=1.75,
                label=f"random, {extra_rate:,.0f} NM²/h (assumed)")
    ax.axhline(0.9, color="#B8872B", lw=1, ls=":")
    ax.set_xlabel("hours on task")
    ax.set_ylabel("probability of detection")
    ax.set_ylim(0, 1)
    ax.set_xlim(0, hours)
    ax.set_title(f"POD in a {plan.area_nm2:,.0f} NM² box at {plan.speed_kt:g} kt", loc="left")
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    ax.legend(frameon=False, loc="lower right")
    fig.tight_layout()
    png_path = out.with_suffix(".png")
    fig.savefig(png_path, facecolor="#F6F4EF")
    plt.close(fig)
    written.append(png_path)
    return written


def cmd_curve(args: argparse.Namespace) -> None:
    plan = SearchPlan(args.area, args.sweep_width, args.speed)
    written = write_curve(plan, args.hours, args.step, Path(args.out), args.alt_rate)
    for path in written:
        print(f"wrote {path}")
    if len(written) == 1:
        print("matplotlib not installed: CSV only (pip install matplotlib for the PNG)")


def cmd_reacquire(args: argparse.Namespace) -> None:
    for gap_min in args.gap_min:
        print(reacquire(args.pod, args.target_speed, gap_min / 60.0, args.sweep_width, args.speed).as_text())
    if args.budget_h:
        gap = max_affordable_gap(args.budget_h, args.pod, args.target_speed, args.sweep_width, args.speed)
        print(f"longest gap recoverable within {args.budget_h:g} h: {gap * 60:.0f} min")


def cmd_burden(args: argparse.Namespace) -> None:
    print(alert_burden(args.candidates, args.pfa, args.targets, args.pd, args.review_s).as_text())


def cmd_cue(args: argparse.Namespace) -> None:
    radius = cue_error_radius(args.error_m, args.age_s, args.target_speed_ms)
    footprint = footprint_width(args.range_m, args.fov)
    result = cue_time(radius, footprint, args.scan_speed, args.slew_deg, args.slew_rate, args.settle_s, args.pod)
    print(f"error radius {radius:.0f} m, footprint {footprint:.0f} m")
    print(result.as_text())


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="isrsearch", description="Search theory for wide-area ISR.")
    sub = parser.add_subparsers(dest="command", required=True)

    def box(p):
        p.add_argument("--area", type=float, required=True, help="search area, NM^2")
        p.add_argument("--sweep-width", type=float, required=True, help="effective sweep width, NM")
        p.add_argument("--speed", type=float, required=True, help="ground speed, kt")

    p = sub.add_parser("plan", help="POD after a time on task")
    box(p)
    p.add_argument("--hours", type=float, required=True)
    p.add_argument("--pod", type=float, help="also report hours for this POD")
    p.set_defaults(func=cmd_plan)

    p = sub.add_parser("footprint", help="staring footprint and area rate")
    p.add_argument("--range-m", type=float, required=True)
    p.add_argument("--fov", type=float, required=True, help="sensor field of view across the footprint, degrees")
    p.add_argument("--speed", type=float, default=80.0, help="platform ground speed, kt")
    p.set_defaults(func=cmd_footprint)

    p = sub.add_parser("curve", help="write POD versus time (CSV, PNG if matplotlib)")
    box(p)
    p.add_argument("--hours", type=float, default=16.0)
    p.add_argument("--step", type=float, default=0.25)
    p.add_argument("--alt-rate", type=float, help="add a curve for an assumed area rate, NM^2/h")
    p.add_argument("--out", default="out/pod_vs_time")
    p.set_defaults(func=cmd_curve)

    p = sub.add_parser("reacquire", help="re-search time after lost contact")
    p.add_argument("--target-speed", type=float, required=True, help="target max speed, kt")
    p.add_argument("--gap-min", type=float, nargs="+", required=True)
    p.add_argument("--sweep-width", type=float, required=True)
    p.add_argument("--speed", type=float, required=True)
    p.add_argument("--pod", type=float, default=0.9)
    p.add_argument("--budget-h", type=float)
    p.set_defaults(func=cmd_reacquire)

    p = sub.add_parser("burden", help="operator false-alarm burden")
    p.add_argument("--candidates", type=float, required=True, help="candidates evaluated per hour")
    p.add_argument("--pfa", type=float, required=True)
    p.add_argument("--targets", type=float, required=True, help="real targets per hour")
    p.add_argument("--pd", type=float, required=True)
    p.add_argument("--review-s", type=float, default=20.0)
    p.set_defaults(func=cmd_burden)

    p = sub.add_parser("cue", help="time for a cued narrow sensor to acquire")
    p.add_argument("--error-m", type=float, required=True, help="cue position error, m")
    p.add_argument("--age-s", type=float, default=0.0)
    p.add_argument("--target-speed-ms", type=float, default=0.0)
    p.add_argument("--range-m", type=float, required=True)
    p.add_argument("--fov", type=float, required=True)
    p.add_argument("--scan-speed", type=float, default=100.0, help="footprint ground scan speed, m/s")
    p.add_argument("--slew-deg", type=float, default=0.0)
    p.add_argument("--slew-rate", type=float, default=30.0)
    p.add_argument("--settle-s", type=float, default=0.0)
    p.add_argument("--pod", type=float, default=0.9)
    p.set_defaults(func=cmd_cue)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        args.func(args)
    except (ValueError, OSError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    return 0
