import math

import pytest

from isrsearch import (
    M_PER_NM,
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


def test_handbook_box_2000_nm2_four_hours():
    # 2,000 NM^2, W = 4 NM (assumed), 80 kt, 4 h on task
    c = coverage_factor(4, 80 * 4, 2000)
    assert c == pytest.approx(0.64)
    assert pod_random(c) == pytest.approx(0.47, abs=0.005)
    assert pod_parallel(c) == pytest.approx(0.58, abs=0.005)


def test_ninety_percent_needs_14_4_hours():
    length = track_length_required(0.9, 2000, 4)
    assert length == pytest.approx(1151, abs=1)
    assert length / 80 == pytest.approx(14.4, abs=0.05)
    assert SearchPlan(2000, 4, 80).hours_for(0.9) == pytest.approx(14.39, abs=0.01)


def test_gimbal_only_needs_28_8_hours():
    assert SearchPlan(2000, 2, 80).hours_for(0.9) == pytest.approx(28.8, abs=0.05)


def test_assumed_wide_area_rate():
    assert time_required(0.9, 2000, 3000) == pytest.approx(1.535, abs=0.005)


def test_staring_footprint_example():
    w = footprint_width(5000, 2)
    assert w == pytest.approx(174.5, abs=0.5)
    assert w / M_PER_NM == pytest.approx(0.094, abs=0.001)
    assert w / M_PER_NM * 80 == pytest.approx(7.5, abs=0.1)
    assert coverage_rate(2, 80) == 160


def test_model_ordering_and_limits():
    for c in (0.1, 0.5, 0.64, 1.0, 2.0):
        assert pod_random(c) < pod_parallel(c)
        assert pod_parallel(c) <= pod_exhaustive(c) + 1e-12
    assert pod_exhaustive(1.5) == 1.0
    assert pod_random(0) == 0.0
    assert pod(0.64, "parallel") == pod_parallel(0.64)
    with pytest.raises(ValueError):
        pod(0.5, "lucky")


def test_diminishing_returns():
    plan = SearchPlan(2000, 4, 80)
    gains = [plan.pod(h + 1) - plan.pod(h) for h in range(0, 12)]
    assert all(later < earlier for earlier, later in zip(gains, gains[1:]))


def test_pod_curve_rows():
    rows = pod_curve(SearchPlan(2000, 4, 80), [0, 4, 8])
    assert rows[0] == (0, 0.0, 0.0)
    assert rows[1][1] == pytest.approx(1 - math.exp(-0.64))


@pytest.mark.parametrize("bad", [0.0, 1.0, 1.5])
def test_bad_pod_rejected(bad):
    with pytest.raises(ValueError):
        track_length_required(bad, 2000, 4)
    with pytest.raises(ValueError):
        time_required(bad, 2000, 320)
