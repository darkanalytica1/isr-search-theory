import pytest

from isrsearch import (
    alert_burden,
    cue_error_radius,
    cue_time,
    max_affordable_gap,
    reacquire,
    reacquisition_time,
    sensor_value,
    uncertainty_area,
)


def test_fifteen_minute_gap_example():
    r = reacquire(0.9, 20, 0.25, 2, 80)
    assert r.radius_nm == pytest.approx(5)
    assert r.area_nm2 == pytest.approx(78.5, abs=0.05)
    assert r.hours == pytest.approx(1.13, abs=0.005)


def test_thirty_minute_gap_quadruples_re_search():
    assert uncertainty_area(20, 0.5) == pytest.approx(314.2, abs=0.05)
    t15 = reacquisition_time(0.9, 20, 0.25, 2, 80)
    t30 = reacquisition_time(0.9, 20, 0.5, 2, 80)
    assert t30 == pytest.approx(4.52, abs=0.01)
    assert t30 / t15 == pytest.approx(4.0)


def test_max_affordable_gap_inverts_reacquisition():
    gap = max_affordable_gap(1.13, 0.9, 20, 2, 80)
    assert gap == pytest.approx(0.25, abs=0.002)


def test_alert_burden_at_sea():
    b = alert_burden(50_000, 0.001, 2, 0.8, 20)
    assert b.false_alerts == pytest.approx(50)
    assert b.true_alerts == pytest.approx(1.6)
    assert b.ppv == pytest.approx(0.031, abs=0.0005)
    assert b.review_s_per_hour == pytest.approx(1032)
    assert b.review_min_per_hour == pytest.approx(17.2)


def test_tenfold_pfa_improvement_makes_it_usable():
    b = alert_burden(50_000, 0.0001, 2, 0.8, 20)
    assert b.false_alerts == pytest.approx(5)
    assert b.ppv == pytest.approx(0.24, abs=0.005)
    assert b.review_s_per_hour == pytest.approx(132)


def test_sensor_value_ranking():
    gimbal = sensor_value(120, 0.9, 0.9, 1.0)
    wide = sensor_value(3000, 0.6, 0.3, 0.5)
    pair = sensor_value(3000, 0.6, 0.9, 0.7)
    assert round(gimbal) == 97
    assert round(wide) == 1080
    assert round(pair) == 2314
    assert pair > wide > gimbal


def test_cue_time_search_dominates_for_stale_cue():
    radius = cue_error_radius(150, 10, 10)
    assert radius == 250
    result = cue_time(radius, 174.5, 100, slew_deg=60, slew_rate_deg_s=30, settle_s=1.5)
    assert result.slew_s == pytest.approx(2.0)
    assert result.search_s == pytest.approx(25.9, abs=0.1)
    assert result.dominant == "search"


def test_cue_single_look_when_footprint_covers_error():
    result = cue_time(50, 175, 100, slew_deg=30, slew_rate_deg_s=30, settle_s=1.0)
    assert result.search_s == 0.0
    assert result.total_s == pytest.approx(2.0)
