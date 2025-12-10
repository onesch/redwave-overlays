import pytest
from unittest.mock import MagicMock

from backend.services.leaderboard.service import (
    Leaderboard,
    CarDataBuilder,
    TimeFormatter,
    CarSorter,
    LAP_RACE_API_PLACEHOLDER,
)


# --- TimeFormatter tests ---


@pytest.mark.parametrize(
    "seconds,expected",
    [
        (75.123, "01:15.123"),
        (0, "--:--.---"),
        (None, "--:--.---"),
    ],
)
def test_time_formatter(seconds, expected):
    assert TimeFormatter.format_lap_time(seconds) == expected


@pytest.mark.parametrize(
    "secs,expected",
    [
        (None, "--:--.---"),
        (-5, "--:--.---"),
        (0, "00:00m"),
        (3600, "01:00:00h"),
        (3665, "01:01:05h"),
        (65, "01:05m"),
    ],
)
def test_format_session_time_edge_cases(secs, expected):
    assert TimeFormatter.format_session_time(secs, is_seconds=True) == expected


# --- CarSorter tests ---


def test_car_sorter_orders_correctly():
    cars = [
        {"pos": 3},
        {"pos": None},
        {"pos": 1},
        {"pos": 0},
    ]
    result = CarSorter.sort(cars)
    assert [c["pos"] for c in result] == [1, 3, 0, None]


# --- CarDataBuilder tests ---


def test_builder_returns_none_for_pace_car(mock_irsdk_leaderboard):
    builder = CarDataBuilder(mock_irsdk_leaderboard)
    drivers = [{"UserName": "PACE CAR"}]
    result = builder.build(
        0,
        drivers,
        [1],
        [1],
        [80.0],
        [5],
        [0.3],
        multiclass=False,
        is_pitroad=[False],
    )
    assert result is None


def test_get_starting_position_from_qualify_stats(mock_irsdk_leaderboard):
    builder = CarDataBuilder(mock_irsdk_leaderboard)
    pos = builder._get_starting_position(car_idx=1, field="Position", offset=0)
    assert pos == 2


def test_get_starting_position_missing_qualify(mock_irsdk_leaderboard):
    builder = CarDataBuilder(mock_irsdk_leaderboard)
    pos = builder._get_starting_position(
        car_idx=999, field="Position", offset=0
    )
    assert pos == 0


def test_starting_position_falls_back_to_race(mock_irsdk_leaderboard):
    builder = CarDataBuilder(mock_irsdk_leaderboard)
    drivers = mock_irsdk_leaderboard.get_value("DriverInfo")["Drivers"]
    positions = mock_irsdk_leaderboard.get_value("CarIdxPosition")
    class_positions = [0, 1, 2]
    last_lap_times = [80.0, 81.0, 82.0]
    laps_started = [5, 4, 3]
    lap_dist_pct = [0.1, 0.2, 0.3]
    is_pitroad = [False, False, False]

    result = builder.build(
        idx=2,
        drivers=drivers,
        positions=positions,
        class_positions=class_positions,
        last_lap_times=last_lap_times,
        laps_started=laps_started,
        lap_dist_pct=lap_dist_pct,
        multiclass=False,
        is_pitroad=is_pitroad,
    )
    assert result["pos"] == 3


def test_builder_converts_minus_one_position_to_none(mock_irsdk_leaderboard):
    builder = CarDataBuilder(mock_irsdk_leaderboard)
    drivers = mock_irsdk_leaderboard.get_value("DriverInfo")["Drivers"]
    positions = [1, -1, 3]
    class_positions = [0, -1, 2]
    last_lap_times = [80.0, 81.0, 82.0]
    laps_started = [5, 4, 3]
    lap_dist_pct = [0.1, 0.2, 0.3]
    is_pitroad = [False, False, False]

    result = builder.build(
        idx=1,
        drivers=drivers,
        positions=positions,
        class_positions=class_positions,
        last_lap_times=last_lap_times,
        laps_started=laps_started,
        lap_dist_pct=lap_dist_pct,
        multiclass=False,
        is_pitroad=is_pitroad,
    )
    assert result["pos"] is None


def test_builder_negative_laps_converted_to_zero(mock_irsdk_leaderboard):
    builder = CarDataBuilder(mock_irsdk_leaderboard)
    drivers = mock_irsdk_leaderboard.get_value("DriverInfo")["Drivers"]
    result = builder.build(
        0,
        drivers,
        [1],
        [0],
        [80],
        [-999],
        [0.5],
        multiclass=False,
        is_pitroad=[False],
    )
    assert result["laps_started"] == 0


def test_builder_lap_dist_pct_negative_becomes_none(mock_irsdk_leaderboard):
    builder = CarDataBuilder(mock_irsdk_leaderboard)
    drivers = mock_irsdk_leaderboard.get_value("DriverInfo")["Drivers"]
    result = builder.build(
        0,
        drivers,
        [1],
        [0],
        [80],
        [1],
        [-0.5],
        multiclass=False,
        is_pitroad=[False],
    )
    assert result["lap_dist_pct"] is None


def test_builder_returns_valid_data(mock_irsdk_leaderboard):
    builder = CarDataBuilder(mock_irsdk_leaderboard)
    drivers = [
        {
            "UserName": "Driver1",
            "CarNumber": "12",
            "IRating": 2000,
            "LicString": "A 4.99",
            "CarClassColor": 16711680,
        }
    ]
    result = builder.build(
        0,
        drivers,
        [1],
        [1],
        [80.0],
        [5],
        [0.3],
        multiclass=False,
        is_pitroad=[False],
    )
    assert result["pos"] == 1
    assert result["car_idx"] == 0
    assert result["car_number"] == "12"
    assert result["name"] == "Driver1"
    assert result["laps_started"] == 5
    assert result["last_lap"] == "01:20.000"
    assert result["irating"] == 2000
    assert result["license"] == "A 4.99"
    assert result["car_class_color"] == 16711680
    assert result["lap_dist_pct"] == 0.3


# --- Leaderboard tests ---


def test_is_lap_race_various_inputs(mock_irsdk_leaderboard):
    leaderboard = Leaderboard(mock_irsdk_leaderboard)
    assert not leaderboard._is_lap_race(None)
    assert leaderboard._is_lap_race("Unlimited")
    assert leaderboard._is_lap_race(LAP_RACE_API_PLACEHOLDER)
    assert not leaderboard._is_lap_race("120 sec")
    assert not leaderboard._is_lap_race(1000.0)
    assert leaderboard._is_lap_race(LAP_RACE_API_PLACEHOLDER + 1)


def test_resolve_session_time_formats_and_approx(mock_irsdk_leaderboard):
    leaderboard = Leaderboard(mock_irsdk_leaderboard)
    current_session = {"SessionType": "RACE", "SessionLaps": 10}
    player_lap_time = 80.0

    result_unformatted = leaderboard._resolve_session_time(
        current_session,
        player_lap_time,
        LAP_RACE_API_PLACEHOLDER,
        format=False,
    )
    assert isinstance(result_unformatted, float)

    result_formatted = leaderboard._resolve_session_time(
        current_session, player_lap_time, LAP_RACE_API_PLACEHOLDER, format=True
    )
    assert isinstance(result_formatted, str)
    assert result_formatted.startswith("~")
    assert result_formatted.endswith("m")


def test_leaderboard_snapshot_structure(mock_irsdk_leaderboard):
    leaderboard = Leaderboard(mock_irsdk_leaderboard)

    result = leaderboard.get_leaderboard_snapshot()
    assert "cars" in result
    assert "player" in result
    assert "neighbors" in result
    assert "leaderboard_data" in result
    assert "timestamp" in result
    assert isinstance(result["timestamp"], int)


def test_leaderboard_snapshot_multiclass(mock_irsdk_leaderboard_multiclass):
    leaderboard = Leaderboard(mock_irsdk_leaderboard_multiclass)
    result = leaderboard.get_leaderboard_snapshot()
    assert result["multiclass"] is True


def test_leaderboard_no_drivers_returns_error():
    irsdk = MagicMock()
    irsdk.get_value.side_effect = lambda key: {
        "DriverInfo": {"Drivers": []}
    }.get(key)
    leaderboard = Leaderboard(irsdk)
    result = leaderboard.get_leaderboard_snapshot()
    assert result == {"error": "No driver/player data"}


def test_get_neighbors_returns_expected(mock_irsdk_leaderboard):
    leaderboard = Leaderboard(mock_irsdk_leaderboard)
    neighbors = leaderboard._get_neighbors(
        player_idx=0,
        drivers=mock_irsdk_leaderboard.get_value("DriverInfo")["Drivers"],
        lap_dist_pct=[0.3, 0.6, 0.1],
    )
    assert "ahead" in neighbors
    assert "behind" in neighbors
    assert isinstance(neighbors["ahead"], list)
    assert isinstance(neighbors["behind"], list)


def test_get_session_info_returns_expected(mock_irsdk_leaderboard):
    leaderboard = Leaderboard(mock_irsdk_leaderboard)
    data = leaderboard._get_session_info(player_idx=0)
    assert data["session_laps"] == "10"
    assert data["session_time"] == 100.0
    assert data["player_lap_time"] == 79.8


def test_get_player_lap_time_returns_fastest_or_est(mock_irsdk_leaderboard):
    leaderboard = Leaderboard(mock_irsdk_leaderboard)
    sessions = [
        {"ResultsFastestLap": [{"CarIdx": 0, "FastestTime": 78.5}]},
        {"ResultsFastestLap": [{"CarIdx": 1, "FastestTime": 81.0}]},
    ]
    assert leaderboard._get_player_lap_time(0, sessions) == 78.5
    assert leaderboard._get_player_lap_time(1, sessions) == 81.0
    assert (
        leaderboard._get_player_lap_time(2, sessions)
        == mock_irsdk_leaderboard.get_value("DriverInfo")["Drivers"][2][
            "CarClassEstLapTime"
        ]
    )


def test_get_last_pit_lap_behavior(mock_irsdk_leaderboard):
    builder = CarDataBuilder(mock_irsdk_leaderboard)
    laps_started = [5, 6]
    is_pitroad = [True, False]

    result_in = builder._get_last_pit_lap(0, laps_started, is_pitroad)
    assert result_in == "L5 IN"

    builder._last_pit_laps[1] = 6
    result_out_first = builder._get_last_pit_lap(
        1, laps_started, [False, False]
    )
    assert result_out_first.startswith("L6 OUT")

    builder._pit_exit_times[1] -= 6
    result_after = builder._get_last_pit_lap(1, laps_started, [False, False])
    assert result_after == "L6"
