import pytest

from backend.services.telemetry.service import (
    TelemetryContext,
    TelemetryService,
)


# --- _build_snapshot tests ---


def test_snapshot_expected_structure(mock_service, mock_ctx):
    snapshot = mock_service._build_snapshot(mock_ctx())

    assert snapshot["status"] == "ok"
    assert snapshot["throttle"] == pytest.approx(0.73)
    assert snapshot["brake"] == pytest.approx(0.11)
    assert snapshot["throttle_pct"] == pytest.approx(73.0)
    assert snapshot["brake_pct"] == pytest.approx(11.0)
    assert snapshot["gear"] == 4
    assert snapshot["speed_ms"] == pytest.approx(246.8)
    assert snapshot["is_brake_abs"] is True


# --- _normalize_pedal tests ---


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


# --- Top Speed and Exit Speed ---


def _ctx(speed, throttle=0.0, brake=0.0) -> TelemetryContext:
    return TelemetryContext(
        throttle=throttle,
        brake=brake,
        gear=3,
        speed_ms=speed,
        is_brake_abs=False,
    )


def _sample(mock_service, mock_ctx, speed, throttle=0.0, brake=0.0):
    """Feed one telemetry sample through the mock_service and return the snapshot."""
    return mock_service._build_snapshot(
        mock_ctx(speed_ms=speed, throttle=throttle, brake=brake)
    )


def test_top_speed_is_peak_speed_before_braking(mock_service, mock_ctx):
    _sample(mock_service, mock_ctx, 200.0, throttle=1.0)
    _sample(mock_service, mock_ctx, 280.0, throttle=1.0)
    _sample(mock_service, mock_ctx, 270.0, throttle=1.0)

    snapshot = _sample(mock_service, mock_ctx, 265.0, brake=0.8)

    assert snapshot["top_speed_ms"] == pytest.approx(280.0)


def test_top_speed_is_held_while_braking(mock_service, mock_ctx):
    _sample(mock_service, mock_ctx, 280.0, throttle=1.0)
    _sample(mock_service, mock_ctx, 250.0, brake=0.8)

    # Speed drops below the braking peak but the latched value stays.
    snapshot = _sample(mock_service, mock_ctx, 120.0, brake=0.9)

    assert snapshot["top_speed_ms"] == pytest.approx(280.0)


def test_top_speed_peak_restarts_after_brake_release(mock_service, mock_ctx):
    _sample(mock_service, mock_ctx, 280.0, throttle=1.0)
    _sample(mock_service, mock_ctx, 120.0, brake=0.9)
    _sample(mock_service, mock_ctx, 130.0, throttle=0.5)
    _sample(mock_service, mock_ctx, 200.0, throttle=1.0)

    snapshot = _sample(mock_service, mock_ctx, 190.0, brake=0.7)

    # The 280 m/s peak belongs to the previous straight.
    assert snapshot["top_speed_ms"] == pytest.approx(200.0)


def test_exit_speed_is_speed_at_first_throttle_after_braking(
    mock_service, mock_ctx
):
    _sample(mock_service, mock_ctx, 150.0, brake=0.9)
    snapshot = _sample(mock_service, mock_ctx, 140.0)

    assert snapshot["exit_speed_ms"] is None

    snapshot = _sample(mock_service, mock_ctx, 145.0, throttle=0.3)
    assert snapshot["exit_speed_ms"] == pytest.approx(145.0)

    # Later throttle input does not overwrite the corner exit speed.
    snapshot = _sample(mock_service, mock_ctx, 180.0, throttle=1.0)
    assert snapshot["exit_speed_ms"] == pytest.approx(145.0)


def test_exit_speed_ignores_throttle_without_prior_braking(
    mock_service, mock_ctx
):
    snapshot = _sample(mock_service, mock_ctx, 200.0, throttle=1.0)

    assert snapshot["exit_speed_ms"] is None


def test_speed_metrics_are_none_before_any_braking(mock_service, mock_ctx):
    snapshot = _sample(mock_service, mock_ctx, 200.0, throttle=1.0)

    assert snapshot["exit_speed_ms"] is None
    assert snapshot["exit_speed_ms"] is None


def test_speed_metrics_reset_on_session_change(irsdk_mock_factory):
    service = TelemetryService(
        irsdk_mock_factory({"WeekendInfo": {"SessionID": 1}, "SessionNum": 0})
    )
    service._build_snapshot(_ctx(280.0, throttle=1.0))
    service._build_snapshot(_ctx(250.0, brake=0.9))
    service._build_snapshot(_ctx(260.0, throttle=0.5))
    assert service.top_speed_ms == pytest.approx(280.0)
    assert service.exit_speed_ms == pytest.approx(260.0)

    service.irsdk = irsdk_mock_factory(
        {"WeekendInfo": {"SessionID": 1}, "SessionNum": 1}
    )
    snapshot = service._build_snapshot(_ctx(100.0, throttle=1.0))

    assert snapshot["top_speed_ms"] is None
    assert snapshot["exit_speed_ms"] is None
