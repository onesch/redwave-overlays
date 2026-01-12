import pytest
from unittest.mock import MagicMock

from backend.services.leaderboard.service import LeaderboardContext
from backend.services.leaderboard.service import (
    Leaderboard,
    CarDataBuilder,
)


# --- CarDataBuilder tests ---


def test_builder_returns_none_for_pace_car(ctx_from_mock, builder):
    ctx = ctx_from_mock(drivers=[{"UserName": "PACE CAR"}])

    result = builder.build(0, ctx)
    assert result is None


def test_reset_pit_data_clears_dicts(builder):
    builder._last_pit_laps = {0: 5}
    builder._pit_exit_times = {0: 1234567890.0}

    builder.reset_pit_data()

    assert builder._last_pit_laps == {}
    assert builder._pit_exit_times == {}


@pytest.mark.parametrize(
    "username,expected",
    [
        ("PACE CAR", True),
        ("pace car", True),
        ("PaCe CaR", True),
        ("Driver1", False),
        ("", False),
    ],
)
def test_is_pace_car_variants(mock_irsdk_leaderboard, username, expected):
    builder = CarDataBuilder(mock_irsdk_leaderboard)
    driver = {"UserName": username}
    assert builder._is_pace_car(driver) is expected


@pytest.mark.parametrize(
    "username,expected",
    [
        ("Driver One", "Driver"),
        (" SingleName ", "SingleName"),
        ("", ""),
        ("   ", ""),
    ],
)
def test_get_first_name_variants(mock_irsdk_leaderboard, username, expected):
    builder = CarDataBuilder(mock_irsdk_leaderboard)
    driver = {"UserName": username}
    assert builder._get_first_name(driver) == expected


@pytest.mark.parametrize(
    "lap_dist,expected",
    [
        (0.4567, 0.457),
        (0.0, 0.0),
        (-0.1, None),
        (None, None),
        ("not_float", None),
    ],
)
def test_format_lap_dist_variants(builder, ctx_from_mock, lap_dist, expected):
    ctx = ctx_from_mock(lap_dist_pct=[lap_dist])
    assert builder._format_lap_dist(0, ctx) == expected


def test_resolve_position_multiclass_zero_and_negative(builder, ctx_from_mock):
    ctx = ctx_from_mock(positions=[0, -1])
    zero_pos = builder._resolve_position(idx=0, ctx=ctx)
    negative_pos = builder._resolve_position(idx=1, ctx=ctx)
    assert zero_pos == 1
    assert negative_pos == None


def test_resolve_position_normal_and_negative(builder, ctx_from_mock):
    ctx = ctx_from_mock(positions=[-1, 3])
    assert builder._resolve_position(0, ctx) is None
    assert builder._resolve_position(1, ctx) == 3


def test_get_starting_position_from_qualify_stats(builder):
    pos = builder._get_starting_position(car_idx=1, field="Position", offset=0)
    assert pos == 2


def test_get_starting_position_missing_qualify(builder):
    pos = builder._get_starting_position(
        car_idx=999, field="Position", offset=0
    )
    assert pos == 0


def test_starting_position_falls_back_to_race(builder, ctx_from_mock):
    ctx = ctx_from_mock(positions=[0])
    result = builder.build(0, ctx)
    assert result["name"] == "Driver1"
    assert result["pos"] == 1


def test_builder_converts_negative_position_to_none(builder, ctx_from_mock):
    NEGATIVE_TO_NONE = -1
    ctx = ctx_from_mock(positions=[NEGATIVE_TO_NONE])
    result = builder.build(0, ctx)
    assert result["pos"] is None


def test_builder_negative_laps_converted_to_zero(builder, ctx_from_mock):
    CONVERTED_TO_ZERO = -999
    ctx = ctx_from_mock(laps_started=[CONVERTED_TO_ZERO])
    result = builder.build(0, ctx)
    assert result["laps_started"] == 0


def test_builder_negative_lap_dist_pct_to_none(builder, ctx_from_mock):
    NEGATIVE_TO_NONE = -9.9
    ctx = ctx_from_mock(lap_dist_pct=[NEGATIVE_TO_NONE])
    result = builder.build(0, ctx)
    assert result["lap_dist_pct"] is None


def test_builder_returns_valid_data(builder, ctx_from_mock):
    drivers = [
        {
            "UserName": "Driver1",
            "CarNumber": "12",
            "IRating": 2000,
            "LicString": "A 4.99",
            "CarClassColor": 16711680,
        }
    ]
    ctx = ctx_from_mock()
    result = builder.build(0, ctx)

    assert result["pos"] == 1
    assert result["car_idx"] == 0
    assert result["car_number"] == "12"
    assert result["name"] == "Driver1"
    assert result["laps_started"] == 5
    assert result["last_lap"] == "01:20.000"
    assert result["irating"] == 2000
    assert result["license"] == "A 4.99"
    assert result["car_class_color"] == 16711680
    assert result["lap_dist_pct"] == 0.6


def test_get_last_pit_lap_behavior(builder):
    laps_started = [5, 6]
    is_pitroad = [True, False]

    result_in = builder._get_last_pit_lap(0, laps_started, is_pitroad)
    assert result_in == "IN L5"

    builder._last_pit_laps[1] = 6
    result_out_first = builder._get_last_pit_lap(
        1, laps_started, [False, False]
    )
    assert result_out_first.startswith("OUT L6")

    builder._pit_exit_times[1] -= 6
    result_after = builder._get_last_pit_lap(1, laps_started, [False, False])
    assert result_after == "L6"
