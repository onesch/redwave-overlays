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


# --- Snapshot tests ---


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
    "clr",
    [
        CLR_LEFT,
        CLR_BOTH,
        CLR_TWO_LEFT,
    ],
)
def test_snapshot_contains_left_alert(
    mock_service,
    mock_ctx,
    clr,
):
    ctx = mock_ctx(car_left_right=clr)

    snapshot = mock_service._build_snapshot(ctx)

    assert snapshot["left"] is not None
    assert "offset" in snapshot["left"]


@pytest.mark.parametrize(
    "clr",
    [
        CLR_RIGHT,
        CLR_BOTH,
        CLR_TWO_RIGHT,
    ],
)
def test_snapshot_contains_right_alert(
    mock_service,
    mock_ctx,
    clr,
):
    ctx = mock_ctx(car_left_right=clr)

    snapshot = mock_service._build_snapshot(ctx)

    assert snapshot["right"] is not None
    assert "offset" in snapshot["right"]


@pytest.mark.parametrize(
    "clr",
    [
        CLR_LEFT,
        CLR_RIGHT,
        CLR_BOTH,
        CLR_TWO_LEFT,
        CLR_TWO_RIGHT,
    ],
)
def test_snapshot_suppresses_front_and_back_when_side_car_present(
    mock_service,
    mock_ctx,
    clr,
):
    ctx = mock_ctx(car_left_right=clr)

    snapshot = mock_service._build_snapshot(ctx)

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


# --- _lap_delta tests ---


def test_lap_delta_ahead():
    assert RadarService._lap_delta(0.45, 0.47) == pytest.approx(0.02)

def test_lap_delta_behind():
    assert RadarService._lap_delta(0.47, 0.45) == pytest.approx(-0.02)

def test_lap_delta_wraparound_ahead():
    # Player at 98%, other at 2% — other is 4% ahead
    assert RadarService._lap_delta(0.98, 0.02) == pytest.approx(0.04)

def test_lap_delta_wraparound_behind():
    # Player at 2%, other at 98% — other is 4% behind
    assert RadarService._lap_delta(0.02, 0.98) == pytest.approx(-0.04)


# --- _find_closest_side_car tests ---


def test_find_closest_side_car_basic(mock_service, mock_ctx):
    # Car 1 at 0.51 is closer than car 2 at 0.60
    ctx = mock_ctx(lap_dist_pct=[0.50, 0.51, 0.60], player_idx=0)
    result = mock_service._find_closest_side_car(ctx)
    assert result == 1

def test_find_closest_side_car_no_player(mock_service, mock_ctx):
    ctx = mock_ctx(player_idx=None)
    assert mock_service._find_closest_side_car(ctx) is None

def test_find_closest_side_car_empty(mock_service, mock_ctx):
    ctx = mock_ctx(lap_dist_pct=[], player_idx=None)
    assert mock_service._find_closest_side_car(ctx) is None


# --- _compute_side_offset tests ---


def test_compute_side_offset_ahead(mock_service, mock_ctx):
    # Car 1 is slightly ahead
    ctx = mock_ctx(lap_dist_pct=[0.50, 0.52], player_idx=0)
    result = mock_service._compute_side_offset(ctx)
    assert result is not None
    assert result["offset"] == pytest.approx(0.02)

def test_compute_side_offset_behind(mock_service, mock_ctx):
    # Car 1 is slightly behind
    ctx = mock_ctx(lap_dist_pct=[0.50, 0.48], player_idx=0)
    result = mock_service._compute_side_offset(ctx)
    assert result is not None
    assert result["offset"] == pytest.approx(-0.02)

def test_compute_side_offset_no_player(mock_service, mock_ctx):
    ctx = mock_ctx(player_idx=None)
    assert mock_service._compute_side_offset(ctx) is None
