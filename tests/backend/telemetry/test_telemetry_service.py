import pytest

from backend.services.telemetry.service import TelemetryService


# --- Positive tests ---


def test_snapshot_expected_structure(mock_service, mock_ctx):
    snapshot = mock_service._build_snapshot(mock_ctx())

    assert snapshot["status"] == "ok"
    assert snapshot["throttle"] == pytest.approx(0.73)
    assert snapshot["brake"] == pytest.approx(0.11)
    assert snapshot["throttle_pct"] == pytest.approx(73.0)
    assert snapshot["brake_pct"] == pytest.approx(11.0)
    assert snapshot["gear"] == 4
    assert snapshot["speed_km"] == pytest.approx(246.8)
    assert snapshot["is_brake_abs"] is True


@pytest.mark.parametrize(
    "raw,expected",
    [
        (0.0, 0.0),
        (0.5, 0.5),
        (1.0, 1.0),
        (-2.0, 0.0),
        (5.0, 1.0),
        (None, 0.0),
        ("0.4", 0.0),
    ],
)
def test_normalize_pedal(raw, expected):
    assert TelemetryService._normalize_pedal(raw) == pytest.approx(expected)


# --- Negative tests ---


def test_build_context_normalizes_invalid_pedals(irsdk_mock_factory):
    values = {
        "Throttle": -1,
        "Brake": 2,
    }
    irsdk = irsdk_mock_factory(values)
    irsdk.get_speed_kmh = lambda: 77.7

    service = TelemetryService(irsdk)
    ctx = service._build_context()

    assert ctx is not None
    assert ctx.throttle == pytest.approx(0.0)
    assert ctx.brake == pytest.approx(1.0)
