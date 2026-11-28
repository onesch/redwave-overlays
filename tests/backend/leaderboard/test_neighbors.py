import pytest

from backend.components.track_position import CarPositionContext
from backend.components.track_time_line import (
    SEGMENTS_PER_LAP,
    TrackTimeLineComponent,
)


# --- collect_candidates ---


def test_collect_candidates_orders_ahead_and_behind_by_distance_gap(
    mock_neighbors,
    mock_ctx,
):
    ctx = mock_ctx(
        drivers=[
            {"UserName": "me", "CarClassID": 1, "CarClassEstLapTime": 100.0},
            {"UserName": "ahead_far", "CarClassID": 1},
            {"UserName": "ahead_close", "CarClassID": 1},
            {"UserName": "behind_far", "CarClassID": 1},
            {"UserName": "behind_close", "CarClassID": 1},
        ],
        positions=[1, 2, 3, 4, 5],
        class_positions=[1, 2, 3, 4, 5],
        lap_dist_pct=[0.5, 0.8, 0.6, 0.2, 0.4],
        laps_started=[5, 5, 5, 5, 5],
        est_times=[50.0, 80.0, 60.0, 20.0, 40.0],
        last_lap_times=[80.0] * 5,
        best_lap_times=[80.0] * 5,
        is_pitroad=[False] * 5,
    )

    ahead, behind = mock_neighbors._collect_candidates(0, ctx)
    ahead, behind = mock_neighbors._sort_candidates(ahead, behind)

    assert [candidate["car"]["name"] for candidate in ahead] == [
        "ahead_close",
        "ahead_far",
    ]
    assert [candidate["car"]["name"] for candidate in behind] == [
        "behind_close",
        "behind_far",
    ]


def test_collect_candidates_wraparound_neighbor_detection(mock_neighbors, mock_ctx):
    ctx = mock_ctx(
        drivers=[
            {"UserName": "me", "CarClassID": 1, "CarClassEstLapTime": 100.0},
            {"UserName": "ahead_across_line", "CarClassID": 1},
            {"UserName": "behind_across_line", "CarClassID": 1},
        ],
        lap_dist_pct=[0.98, 0.02, 0.95],
        laps_started=[5, 6, 5],
        est_times=[98.0, 2.0, 95.0],
        positions=[1, 2, 3],
        class_positions=[1, 2, 3],
        last_lap_times=[80.0] * 3,
        best_lap_times=[80.0] * 3,
        is_pitroad=[False] * 3,
    )

    ahead, behind = mock_neighbors._collect_candidates(0, ctx)

    assert ahead[0]["car"]["name"] == "ahead_across_line"
    assert ahead[0]["gap_pct"] == pytest.approx(0.04)
    assert ahead[0]["gap_sec"] == pytest.approx(4.0)
    assert behind[0]["car"]["name"] == "behind_across_line"
    assert behind[0]["gap_pct"] == pytest.approx(-0.03)
    assert behind[0]["gap_sec"] == pytest.approx(-3.0)



def test_other_class_cars_are_kept_in_neighbors_by_track_position(
    mock_neighbors,
    mock_ctx,
):
    ctx = mock_ctx(
        drivers=[
            {"UserName": "me", "CarClassID": 1, "CarClassEstLapTime": 100.0},
            {"UserName": "same_class", "CarClassID": 1},
            {
                "UserName": "traffic_ahead",
                "CarClassID": 2,
                "CarClassEstLapTime": 80.0,
            },
            {
                "UserName": "traffic_behind",
                "CarClassID": 2,
                "CarClassEstLapTime": 80.0,
            },
        ],
        lap_dist_pct=[0.5, 0.6, 0.7, 0.4],
        laps_started=[5, 5, 5, 5],
        est_times=[50.0, 60.0, 56.0, 32.0],
        positions=[1, 2, 3, 4],
        class_positions=[1, 2, 1, 2],
        last_lap_times=[80.0] * 4,
        best_lap_times=[80.0] * 4,
        is_pitroad=[False] * 4,
        multiclass=True,
    )

    neighbors = mock_neighbors.get_neighbors(0, ctx)

    assert [car["name"] for car in neighbors["ahead"]] == [
        "same_class",
        "traffic_ahead",
    ]
    assert [car["name"] for car in neighbors["behind"]] == ["traffic_behind"]
    assert neighbors["ahead"][0]["same_class"] is True
    assert neighbors["ahead"][1]["same_class"] is False
    assert neighbors["ahead"][1]["gap_sec"] == pytest.approx(20.0)
    assert neighbors["behind"][0]["same_class"] is False


def make_traffic_ctx(mock_ctx, **overrides):
    """The player, a GT3 car of another model and a car of another class."""
    values = dict(
        drivers=[
            {"UserName": "me", "CarClassID": 1, "CarClassEstLapTime": 100.0},
            # Same class, another car model: a 2% slower reference lap.
            {"UserName": "same_class", "CarClassID": 1, "CarClassEstLapTime": 102.0},
            {
                "UserName": "traffic_ahead",
                "CarClassID": 2,
                "CarClassEstLapTime": 80.0,
            },
        ],
        lap_dist_pct=[0.5, 0.6, 0.7],
        laps_started=[5, 5, 5],
        est_times=[50.0, 61.2, 56.0],
        positions=[1, 2, 3],
        class_positions=[1, 2, 1],
        last_lap_times=[80.0] * 3,
        best_lap_times=[80.0] * 3,
        is_pitroad=[False] * 3,
        multiclass=True,
    )
    values.update(overrides)
    return mock_ctx(**values)


def test_time_gaps_to_every_car_come_from_the_time_line(mock_neighbors, mock_ctx):
    # The player's car is slow between 0.5 and 0.7: 0.2 lap takes 30 s,
    # not the 20 s of the average pace (100 s lap).
    time_line = TrackTimeLineComponent()
    time_line.bind("track", 1, 100.0)
    for segment in range(SEGMENTS_PER_LAP):
        pct = (segment + 0.5) / SEGMENTS_PER_LAP
        time_line.record(
            CarPositionContext(
                lap_dist_pct=pct,
                est_time=pct * 100 + min(max(pct - 0.5, 0), 0.2) * 50,
                est_lap_time=100.0,
            )
        )

    neighbors = mock_neighbors.get_neighbors(
        0, make_traffic_ctx(mock_ctx, track_time_line=time_line)
    )
    gaps = {car["name"]: car["gap_sec"] for car in neighbors["ahead"]}

    # 0.1 lap into the slow part takes 15 s, 0.2 lap takes 30 s.
    assert gaps["same_class"] == pytest.approx(15.0, abs=0.05)
    assert gaps["traffic_ahead"] == pytest.approx(30.0, abs=0.05)


def test_time_gaps_fall_back_until_the_time_line_has_data(mock_neighbors, mock_ctx):
    neighbors = mock_neighbors.get_neighbors(0, make_traffic_ctx(mock_ctx))
    gaps = {car["name"]: car["gap_sec"] for car in neighbors["ahead"]}

    # Same class: CarIdxEstTime rescaled from the 102 s car model,
    # 61.2 * 100 / 102 - 50 = 10 s. Another class: 0.2 lap * 100 s.
    assert gaps["same_class"] == pytest.approx(10.0)
    assert gaps["traffic_ahead"] == pytest.approx(20.0)


def test_collect_candidates_skips_missing_or_invalid_telemetry(mock_neighbors, mock_ctx):
    ctx = mock_ctx(
        drivers=[
            {"UserName": "me", "CarClassID": 1, "CarClassEstLapTime": 100.0},
            {"UserName": "valid", "CarClassID": 1},
            {"UserName": "missing_est_time", "CarClassID": 1},
        ],
        lap_dist_pct=[0.5, 0.6, "bad"],
        laps_started=[5, 5, 5],
        est_times=[50.0, 60.0],
        positions=[1, 2, 3],
        class_positions=[1, 2, 3],
        last_lap_times=[80.0] * 3,
        best_lap_times=[80.0] * 3,
        is_pitroad=[False] * 3,
    )

    ahead, behind = mock_neighbors._collect_candidates(0, ctx)

    assert [candidate["car"]["name"] for candidate in ahead] == ["valid"]
    assert behind == []


def test_collect_candidates_returns_empty_for_invalid_player_telemetry(
    mock_neighbors,
    mock_ctx,
):
    ctx = mock_ctx(lap_dist_pct=[-1, 0.6], laps_started=[5, 5], est_times=[50.0, 60.0])

    assert mock_neighbors._collect_candidates(0, ctx) == ([], [])
    assert mock_neighbors._collect_candidates(99, ctx) == ([], [])


# --- sort_candidates ---


def test_sort_candidates(mock_neighbors):
    ahead = [{"gap_pct": 0.3}, {"gap_pct": 0.1}, {"gap_pct": 0.2}]
    behind = [{"gap_pct": -0.3}, {"gap_pct": -0.1}, {"gap_pct": -0.2}]
    sorted_ahead, sorted_behind = mock_neighbors._sort_candidates(
        ahead, behind
    )
    assert [c["gap_pct"] for c in sorted_ahead] == [0.1, 0.2, 0.3]
    assert [c["gap_pct"] for c in sorted_behind] == [-0.1, -0.2, -0.3]


# --- format_neighbors ---


def test_format_neighbors_rounding(mock_neighbors):
    ahead = [
        {"car": {"name": "Driver2"}, "gap_pct": 0.12345, "gap_sec": 12.3456}
    ]
    behind = [
        {"car": {"name": "Driver3"}, "gap_pct": -0.98765, "gap_sec": -98.765}
    ]
    formatted = mock_neighbors._format_neighbors(ahead, behind, limit=1)
    assert formatted["ahead"][0]["gap_pct"] == pytest.approx(0.1235)
    assert formatted["ahead"][0]["gap_sec"] == pytest.approx(12.35)
    assert formatted["behind"][0]["gap_pct"] == pytest.approx(0.9877)
    assert formatted["behind"][0]["gap_sec"] == pytest.approx(98.77)


# --- get_neighbors ---


def test_get_neighbors_returns_expected_keys(mock_neighbors, mock_ctx):
    neighbors = mock_neighbors.get_neighbors(player_idx=0, ctx=mock_ctx())
    assert set(neighbors) == {"ahead", "behind"}
    assert all("name" in c for c in neighbors["ahead"] + neighbors["behind"])


# --- lap flags ---


def test_neighbors_take_lap_flags_from_context_lap_deltas(
    mock_neighbors,
    mock_ctx,
):
    ctx = mock_ctx(
        drivers=[
            {"UserName": "me", "CarClassID": 1, "CarClassEstLapTime": 100.0},
            {"UserName": "lap_ahead", "CarClassID": 1},
            {"UserName": "same_lap", "CarClassID": 1},
            {"UserName": "lap_behind", "CarClassID": 1},
        ],
        lap_dist_pct=[0.5, 0.6, 0.7, 0.4],
        laps_started=[5, 6, 5, 4],
        est_times=[50.0, 60.0, 70.0, 40.0],
        positions=[1, 2, 3, 4],
        class_positions=[1, 2, 3, 4],
        last_lap_times=[80.0] * 4,
        best_lap_times=[80.0] * 4,
        is_pitroad=[False] * 4,
        lap_deltas={1: 1, 2: 0, 3: -1},
    )

    neighbors = mock_neighbors.get_neighbors(0, ctx)
    lap_flags = {
        car["name"]: (car["is_lap_ahead"], car["is_lap_behind"])
        for car in neighbors["ahead"] + neighbors["behind"]
    }

    assert lap_flags == {
        "lap_ahead": (True, False),
        "same_lap": (False, False),
        "lap_behind": (False, True),
    }
