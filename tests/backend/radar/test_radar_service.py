import pytest

from backend.services.radar.service import (
    RadarService,
    DistanceSeverity,
)
from backend.services.radar.constants import (
    CLR_LEFT,
    CLR_RIGHT,
    CLR_BOTH,
    CLR_TWO_LEFT,
    CLR_TWO_RIGHT,
    MAX_SHOW_DIST,
)


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
    assert "offset_ratio" in snapshot["left"]


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
    assert "offset_ratio" in snapshot["right"]


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


# --- _build_context tests ---


def test_build_context(mock_service):
    ctx = mock_service._build_context()

    assert ctx is not None
    assert ctx.dist_ahead == pytest.approx(5.0)
    assert ctx.dist_behind == pytest.approx(6.0)
    assert ctx.car_left_right == 0
    assert ctx.lap_dist_pct == [0.50, 0.51]
    assert ctx.player_idx == 0
    assert ctx.track_length_m == pytest.approx(3992.7)


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
    ctx = mock_ctx(
        lap_dist_pct=[0.50, 0.51, 0.60],
        player_idx=0,
    )
    result = mock_service._find_closest_side_car(ctx)
    assert result == 1


def test_find_closest_side_car_no_player(mock_service, mock_ctx):
    ctx = mock_ctx(player_idx=None)
    assert mock_service._find_closest_side_car(ctx) is None


def test_find_closest_side_car_empty(mock_service, mock_ctx):
    ctx = mock_ctx(
        lap_dist_pct=[],
        player_idx=None,
    )
    assert mock_service._find_closest_side_car(ctx) is None


# --- _compute_side_offset tests ---


def test_compute_side_offset_ahead(mock_service, mock_ctx):
    # Car 1 is 2% of a lap ahead on a 4000 m track.
    # 0.02 * 4000 = 80 m, which is clamped to SIDE_WINDOW_M (8 m).
    # 8 / 8 = 1.0.
    ctx = mock_ctx(
        lap_dist_pct=[0.50, 0.52],
        player_idx=0,
        track_length_m=4000.0,
    )

    result = mock_service._compute_side_offset(ctx)

    assert result is not None
    assert result["offset_ratio"] == pytest.approx(1.0)


def test_compute_side_offset_behind(mock_service, mock_ctx):
    # Car 1 is 2% of a lap behind on a 4000 m track.
    # -0.02 * 4000 = -80 m, which is clamped to -SIDE_WINDOW_M (-8 m).
    # -8 / 8 = -1.0.
    ctx = mock_ctx(
        lap_dist_pct=[0.50, 0.48],
        player_idx=0,
        track_length_m=4000.0,
    )

    result = mock_service._compute_side_offset(ctx)

    assert result is not None
    assert result["offset_ratio"] == pytest.approx(-1.0)


def test_compute_side_offset_within_window(mock_service, mock_ctx):
    # Car 1 is 0.1% of a lap ahead on a 4000 m track.
    # 0.001 * 4000 = 4 m.
    # 4 / 8 = 0.5.
    ctx = mock_ctx(
        lap_dist_pct=[0.50, 0.501],
        player_idx=0,
        track_length_m=4000.0,
    )

    result = mock_service._compute_side_offset(ctx)

    assert result is not None
    assert result["offset_ratio"] == pytest.approx(0.5)


def test_compute_side_offset_depends_on_track_length(
    mock_service,
    mock_ctx,
):
    # The same percentage difference produces different physical
    # distances depending on track length.
    # 0.001 * 4000 = 4 m -> 4 / 8 = 0.5
    # 0.001 * 6000 = 6 m -> 6 / 8 = 0.75
    ctx_short = mock_ctx(
        lap_dist_pct=[0.50, 0.501],
        player_idx=0,
        track_length_m=4000.0,
    )
    ctx_long = mock_ctx(
        lap_dist_pct=[0.50, 0.501],
        player_idx=0,
        track_length_m=6000.0,
    )

    short_result = mock_service._compute_side_offset(ctx_short)
    long_result = mock_service._compute_side_offset(ctx_long)

    assert short_result is not None
    assert long_result is not None

    assert short_result["offset_ratio"] == pytest.approx(0.5)
    assert long_result["offset_ratio"] == pytest.approx(0.75)


def test_compute_side_offset_clamps_to_window(
    mock_service,
    mock_ctx,
):
    # Both physical offsets exceed SIDE_WINDOW_M, so they are clamped
    # to 8 m and both produce the maximum offset_ratio of 1.0.
    # 0.02 * 4000 = 80 m -> 8 / 8 = 1.0
    # 0.02 * 6000 = 120 m -> 8 / 8 = 1.0
    ctx_short = mock_ctx(
        lap_dist_pct=[0.50, 0.52],
        player_idx=0,
        track_length_m=4000.0,
    )
    ctx_long = mock_ctx(
        lap_dist_pct=[0.50, 0.52],
        player_idx=0,
        track_length_m=6000.0,
    )

    short_result = mock_service._compute_side_offset(ctx_short)
    long_result = mock_service._compute_side_offset(ctx_long)

    assert short_result is not None
    assert long_result is not None
    assert short_result["offset_ratio"] == pytest.approx(1.0)
    assert long_result["offset_ratio"] == pytest.approx(1.0)


def test_compute_side_offset_no_player(mock_service, mock_ctx):
    ctx = mock_ctx(player_idx=None)
    assert mock_service._compute_side_offset(ctx) is None


def test_compute_side_offset_no_track_length(
    mock_service,
    mock_ctx,
):
    ctx = mock_ctx(
        lap_dist_pct=[0.50, 0.52],
        player_idx=0,
        track_length_m=None,
    )

    assert mock_service._compute_side_offset(ctx) is None


# --- _parse_track_length tests ---


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("3.9927 km", 3992.7),
        ("4.02 km", 4020.0),
        ("5 km", 5000.0),
    ],
)
def test_parse_track_length(value, expected):
    assert RadarService._parse_track_length(value) == pytest.approx(expected)


@pytest.mark.parametrize(
    "value",
    [
        None,
        "",
        "invalid",
        "abc km",
    ],
)
def test_parse_track_length_invalid(value):
    assert RadarService._parse_track_length(value) is None


# --- DistanceSeverity.is_nearby tests ---


@pytest.mark.parametrize(
    ("dist", "expected"),
    [
        (None, None),
        (-1.0, None),
        (0.0, 0.0),
        (4.5, 4.5),
        (15.0, 15.0),
        (15.1, None),
    ],
)
def test_sanitize_distance(dist, expected):
    assert DistanceSeverity._sanitize_distance(dist) == expected


@pytest.mark.parametrize(
    ("dist", "expected"),
    [
        (None, (None, "none")),
        (-1.0, (None, "none")),
        (4.0, (4.0, "red")),
        (5.0, (5.0, "yellow")),
        (10.0, (10.0, "ok")),
        (MAX_SHOW_DIST, (MAX_SHOW_DIST, "ok")),
        (20.0, (None, "none")),
    ],
)
def test_format_meta(dist, expected):
    assert DistanceSeverity.format_meta(dist) == expected


@pytest.mark.parametrize(
    ("dist", "expected"),
    [
        (None, False),
        (-1.0, False),
        (0.0, True),
        (5.0, True),
        (MAX_SHOW_DIST, True),
        (MAX_SHOW_DIST + 0.1, False),
    ],
)
def test_is_nearby(dist, expected):
    assert DistanceSeverity.is_nearby(dist) is expected
