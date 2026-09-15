import builtins
import csv

import pytest

from isrsearch.cli import main


def test_plan_command(capsys):
    assert main(["plan", "--area", "2000", "--sweep-width", "4", "--speed", "80", "--hours", "4"]) == 0
    out = capsys.readouterr().out
    assert "C = 0.64" in out
    assert "POD random        0.47" in out
    assert "hours for POD 0.9 (random)  14.4" in out


def test_curve_writes_csv_without_matplotlib(tmp_path, monkeypatch, capsys):
    real_import = builtins.__import__

    def no_matplotlib(name, *args, **kwargs):
        if name.startswith("matplotlib"):
            raise ImportError("matplotlib hidden for this test")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", no_matplotlib)
    out = tmp_path / "pod"
    assert main(["curve", "--area", "2000", "--sweep-width", "4", "--speed", "80",
                 "--hours", "16", "--step", "0.5", "--out", str(out)]) == 0
    text = capsys.readouterr().out
    assert "CSV only" in text
    assert not (tmp_path / "pod.png").exists()
    with (tmp_path / "pod.csv").open() as handle:
        rows = list(csv.DictReader(handle))
    assert len(rows) == 33
    at_4h = next(r for r in rows if float(r["hours"]) == 4.0)
    assert float(at_4h["pod_random"]) == pytest.approx(0.4727, abs=1e-4)


def test_curve_writes_png_when_matplotlib_present(tmp_path, capsys):
    pytest.importorskip("matplotlib")
    out = tmp_path / "pod"
    assert main(["curve", "--area", "2000", "--sweep-width", "4", "--speed", "80",
                 "--alt-rate", "3000", "--out", str(out)]) == 0
    assert (tmp_path / "pod.png").stat().st_size > 1000
    header = (tmp_path / "pod.csv").read_text().splitlines()[0]
    assert header.endswith("pod_random_alt_rate")


def test_other_commands(capsys):
    assert main(["reacquire", "--target-speed", "20", "--gap-min", "15", "30",
                 "--sweep-width", "2", "--speed", "80", "--budget-h", "1"]) == 0
    out = capsys.readouterr().out
    assert "re-search 1.13 h" in out and "re-search 4.52 h" in out
    assert main(["burden", "--candidates", "50000", "--pfa", "0.001", "--targets", "2", "--pd", "0.8"]) == 0
    assert "PPV                     0.031" in capsys.readouterr().out
    assert main(["footprint", "--range-m", "5000", "--fov", "2"]) == 0
    assert "175 m" in capsys.readouterr().out
    assert main(["cue", "--error-m", "150", "--age-s", "10", "--target-speed-ms", "10",
                 "--range-m", "5000", "--fov", "2", "--slew-deg", "60", "--settle-s", "1.5"]) == 0
    assert "dominant: search" in capsys.readouterr().out


def test_errors_return_code(capsys):
    assert main(["plan", "--area", "-1", "--sweep-width", "4", "--speed", "80", "--hours", "1"]) == 2
