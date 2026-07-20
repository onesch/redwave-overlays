import pytest


# --- calc_gap ---


def calc_gap(mock_neighbors, **overrides):
    values = {
        "my_dist": 0.2,
        "my_laps": 5,
        "my_est_time": 16.0,
        "my_est_lap_time": 80.0,
        "dist": 0.5,
        "other_laps": 5,
        "other_est_time": 40.0,
    }
    values.update(overrides)
    return mock_neighbors._calc_gap(**values)


def test_calc_gap_basic(mock_neighbors):
    result = calc_gap(mock_neighbors)
    assert result["gap_pct"] == pytest.approx(0.3)
    assert result["gap_sec"] == pytest.approx(24.0)


@pytest.mark.parametrize(
    "my_dist,dist,expected_pct,expected_sec",
    [
        (0.98, 0.02, 0.04, 4.0),
        (0.02, 0.98, -0.04, -4.0),
    ],
)
def test_calc_gap_corrects_start_finish_wraparound(
    mock_neighbors,
    my_dist,
    dist,
    expected_pct,
    expected_sec,
):
    result = calc_gap(
        mock_neighbors,
        my_dist=my_dist,
        my_est_time=my_dist * 100,
        my_est_lap_time=100.0,
        dist=dist,
        other_est_time=dist * 100,
    )
    assert result["gap_pct"] == pytest.approx(expected_pct)
    assert result["gap_sec"] == pytest.approx(expected_sec)


@pytest.mark.parametrize(
    "field,value",
    [
        ("dist", -1),
        ("dist", "abc"),
        ("dist", None),
        ("my_dist", -1),
        ("my_dist", "abc"),
        ("my_dist", None),
    ],
)
def test_calc_gap_invalid_distances(mock_neighbors, field, value):
    assert calc_gap(mock_neighbors, **{field: value}) is None


@pytest.mark.parametrize(
    "field,value",
    [
        ("my_est_time", 0),
        ("my_est_time", -1),
        ("other_est_time", 0),
        ("other_est_time", -1),
    ],
)
def test_calc_gap_invalid_est_times_keep_physical_gap(mock_neighbors, field, value):
    result = calc_gap(mock_neighbors, **{field: value})
    assert result["gap_pct"] == pytest.approx(0.3)
    assert result["gap_sec"] is None


# --- collect_candidates ---


def test_collect_candidates_orders_ahead_and_behind_by_physical_gap(
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

    ahead, behind, _, _ = mock_neighbors._collect_candidates(0, ctx)
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

    ahead, behind, _, _ = mock_neighbors._collect_candidates(0, ctx)

    assert ahead[0]["car"]["name"] == "ahead_across_line"
    assert ahead[0]["gap_pct"] == pytest.approx(0.04)
    assert ahead[0]["gap_sec"] == pytest.approx(4.0)
    assert behind[0]["car"]["name"] == "behind_across_line"
    assert behind[0]["gap_pct"] == pytest.approx(-0.03)
    assert behind[0]["gap_sec"] == pytest.approx(-3.0)



def test_multiclass_traffic_is_separated_but_kept_in_neighbors(
    mock_neighbors,
    mock_ctx,
):
    ctx = mock_ctx(
        drivers=[
            {"UserName": "me", "CarClassID": 1, "CarClassEstLapTime": 100.0},
            {"UserName": "same_class", "CarClassID": 1},
            {"UserName": "traffic_ahead", "CarClassID": 2},
            {"UserName": "traffic_behind", "CarClassID": 2},
        ],
        lap_dist_pct=[0.5, 0.6, 0.7, 0.4],
        laps_started=[5, 5, 5, 5],
        est_times=[50.0, 60.0, 70.0, 40.0],
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
    assert [car["name"] for car in neighbors["physical_ahead"]] == [
        "traffic_ahead"
    ]
    assert [car["name"] for car in neighbors["physical_behind"]] == [
        "traffic_behind"
    ]
    assert neighbors["physical_ahead"][0]["same_class"] is False
    assert neighbors["physical_ahead"][0]["racing_relevance"] == "traffic"


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

    ahead, behind, physical_ahead, physical_behind = mock_neighbors._collect_candidates(
        0,
        ctx,
    )

    assert [candidate["car"]["name"] for candidate in ahead] == ["valid"]
    assert behind == []
    assert physical_ahead == []
    assert physical_behind == []


def test_collect_candidates_returns_empty_for_invalid_player_telemetry(
    mock_neighbors,
    mock_ctx,
):
    ctx = mock_ctx(lap_dist_pct=[-1, 0.6], laps_started=[5, 5], est_times=[50.0, 60.0])

    assert mock_neighbors._collect_candidates(0, ctx) == ([], [], [], [])
    assert mock_neighbors._collect_candidates(99, ctx) == ([], [], [], [])


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
    assert set(neighbors) == {
        "ahead",
        "behind",
        "physical_ahead",
        "physical_behind",
    }
    assert all("name" in c for c in neighbors["ahead"] + neighbors["behind"])
