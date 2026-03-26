import pytest

from backend.services.radar.service import RadarService
from backend.services.radar.constants import (
    CLR_LEFT,
    CLR_RIGHT,
    CLR_BOTH,
    CLR_TWO_LEFT,
    CLR_TWO_RIGHT,
)


# --- Positive tests ---


def test_snapshot_default(mock_service, mock_ctx):
    ctx = mock_ctx()
    snapshot = mock_service._build_snapshot(ctx)
    assert snapshot["status"] == "ok"
    assert snapshot["ahead_m"] == pytest.approx(5.0)
    assert snapshot["behind_m"] == pytest.approx(6.0)
    assert snapshot["ahead_severity"] == "yellow"
    assert snapshot["behind_severity"] == "yellow"
    assert snapshot["left"] is None
    assert snapshot["right"] is None


@pytest.mark.parametrize(
    "clr,left,right",
    [
        (CLR_LEFT, {"severity": "red"}, None),
        (CLR_RIGHT, None, {"severity": "red"}),
        (CLR_BOTH, {"severity": "red"}, {"severity": "red"}),
        (CLR_TWO_LEFT, {"severity": "red"}, None),
        (CLR_TWO_RIGHT, None, {"severity": "red"}),
    ]
)
def test_snapshot_side_alerts(mock_service, mock_ctx, clr, left, right):
    ctx = mock_ctx(car_left_right=clr)
    snapshot = mock_service._build_snapshot(ctx)
    assert snapshot["left"] == left
    assert snapshot["right"] == right
    # Distances should be suppressed
    assert snapshot["ahead_m"] is None
    assert snapshot["behind_m"] is None


def test_snapshot_distance_sanitization(mock_service, mock_ctx):
    # Distances out of range should become None and severity "none"
    ctx = mock_ctx(dist_ahead=20.0, dist_behind=-1.0)
    snapshot = mock_service._build_snapshot(ctx)
    assert snapshot["ahead_m"] is None
    assert snapshot["ahead_severity"] == "none"
    assert snapshot["behind_m"] is None
    assert snapshot["behind_severity"] == "none"


# --- Negative tests ---


def test_distances_out_of_range(irsdk_mock_factory):
    values = {
            "CarDistAhead": 20.0,
            "CarDistBehind": -1.0,
            "CarLeftRight": 0,
        }
    service = RadarService(irsdk_mock_factory(values))
    snapshot = service.get_snapshot()
    assert snapshot["ahead_m"] is None
    assert snapshot["ahead_severity"] == "none"
    assert snapshot["behind_m"] is None
    assert snapshot["behind_severity"] == "none"
