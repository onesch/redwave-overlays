import pytest


def test_calc_gap_basic(neighbors):
    # gap_pct = (0.5 - 0.2) % 1.0 = 0.3
    result = neighbors._calc_gap(my_dist=0.2, dist=0.5, est_lap_time=90.0)
    assert result == {"gap_pct": 0.3, "gap_sec": 27.0}


@pytest.mark.parametrize(
    "dist,expected",
    [
        (-1, None),
        ("abc", None),
        (None, None),
    ],
)
def test_calc_gap_invalid_dist(neighbors, dist, expected):
    assert (
        neighbors._calc_gap(my_dist=0.5, dist=dist, est_lap_time=80.0)
        is expected
    )


def test_collect_candidates_basic(neighbors, builder, ctx_from_mock):
    ctx = ctx_from_mock(
        drivers=[
            {"UserName": "me", "CarClassEstLapTime": 80.0},
            {"UserName": "ahead", "CarClassEstLapTime": 80.0},
            {"UserName": "behind", "CarClassEstLapTime": 80.0},
        ],
        lap_dist_pct=[0.5, 0.9, 0.1],
        laps_started=[5, 5, 5],
    )

    ahead, behind = neighbors._collect_candidates(player_idx=0, ctx=ctx)
    # ahead: dist > my_dist и gap_pct <= 0.5 -> idx 1
    # behind: dist < my_dist -> gap_pct > 0.5 -> idx 2
    assert len(ahead) == 1
    assert len(behind) == 1
    assert ahead[0]["car"]["name"] == "ahead"
    assert behind[0]["car"]["name"] == "behind"


def test_sort_candidates(neighbors):
    # ahead is sorted in ascending order by gap_pct
    # behind is sorted in descending order by gap_pct
    ahead = [{"gap_pct": 0.3}, {"gap_pct": 0.1}, {"gap_pct": 0.2}]
    behind = [{"gap_pct": -0.3}, {"gap_pct": -0.1}, {"gap_pct": -0.2}]
    sorted_ahead, sorted_behind = neighbors._sort_candidates(ahead, behind)
    assert [c["gap_pct"] for c in sorted_ahead] == [0.1, 0.2, 0.3]
    assert [c["gap_pct"] for c in sorted_behind] == [-0.1, -0.2, -0.3]


def test_format_neighbors_rounding(neighbors, ctx_from_mock):
    # gap_pct is rounded to 3 digits
    # gap_sec is rounded to 2 digits
    ahead = [
        {"car": {"name": "Driver2"}, "gap_pct": 0.12345, "gap_sec": 12.3456}
    ]
    behind = [
        {"car": {"name": "Driver3"}, "gap_pct": -0.98765, "gap_sec": -98.765}
    ]
    formatted = neighbors._format_neighbors(ahead, behind, limit=1)
    assert formatted["ahead"][0]["gap_pct"] == 0.123
    assert formatted["ahead"][0]["gap_sec"] == 12.35
    assert formatted["behind"][0]["gap_pct"] == 0.988
    assert formatted["behind"][0]["gap_sec"] == 98.77


def test_get_neighbors_returns_expected(neighbors, ctx_from_mock):
    ctx = ctx_from_mock(
        drivers=[
            {"UserName": "me", "CarClassEstLapTime": 80.0},
            {"UserName": "ahead", "CarClassEstLapTime": 80.0},
            {"UserName": "behind", "CarClassEstLapTime": 80.0},
        ],
        lap_dist_pct=[0.5, 0.9, 0.1],
        laps_started=[5, 5, 5],
    )
    neighbors = neighbors.get_neighbors(player_idx=0, ctx=ctx)
    assert "ahead" in neighbors
    assert "behind" in neighbors
    assert isinstance(neighbors["ahead"], list)
    assert isinstance(neighbors["behind"], list)
    assert all("name" in c for c in neighbors["ahead"] + neighbors["behind"])
