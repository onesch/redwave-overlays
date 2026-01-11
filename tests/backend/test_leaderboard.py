import pytest
from unittest.mock import MagicMock

from backend.services.leaderboard.service import LeaderboardContext
from backend.services.leaderboard.service import (
    Leaderboard,
    CarDataBuilder,
    TimeFormatter,
    CarSorter,
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

    ctx = LeaderboardContext(
        drivers=[{"UserName":"PACE CAR"}],
        positions=[1],
        class_positions=[1],
        last_lap_times=[80.0],
        laps_started=[5],
        lap_dist_pct=[0.3],
        is_pitroad=[False],
        multiclass=False,
    )

    result = builder.build(0, ctx)
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

    ctx = LeaderboardContext(
        drivers=[{"UserName": "Driver1"}],
        positions=[0],
        class_positions=[5],
        last_lap_times=[80.0],
        laps_started=[10],
        lap_dist_pct=[0.4],
        is_pitroad=[False],
        multiclass=False,
    )

    result = builder.build(0, ctx)

    assert result["name"] == "Driver1"
    assert result["pos"] == 1


def test_builder_converts_negative_position_to_none(mock_irsdk_leaderboard):
    builder = CarDataBuilder(mock_irsdk_leaderboard)

    NEGATIVE_TO_NONE = -1

    ctx = LeaderboardContext(
        drivers=mock_irsdk_leaderboard.get_value("DriverInfo")["Drivers"],
        positions=[1, NEGATIVE_TO_NONE, 3],
        class_positions=[0, NEGATIVE_TO_NONE, 2],
        last_lap_times=[80.0, 81.0, 82.0],
        laps_started=[5, 4, 3],
        lap_dist_pct=[0.1, 0.2, 0.3],
        is_pitroad=[False, False, False],
        multiclass=False,
    )

    result = builder.build(1, ctx)
    assert result["pos"] is None


def test_builder_negative_laps_converted_to_zero(mock_irsdk_leaderboard):
    builder = CarDataBuilder(mock_irsdk_leaderboard)
    drivers = mock_irsdk_leaderboard.get_value("DriverInfo")["Drivers"]

    CONVERTED_TO_ZERO = -999

    ctx = LeaderboardContext(
        drivers=drivers,
        positions=[1],
        class_positions=[0],
        last_lap_times=[80],
        laps_started=[CONVERTED_TO_ZERO],
        lap_dist_pct=[0.5],
        is_pitroad=[False],
        multiclass=False,
    )

    result = builder.build(0, ctx)
    assert result["laps_started"] == 0


def test_builder_negative_lap_dist_pct_to_none(mock_irsdk_leaderboard):
    builder = CarDataBuilder(mock_irsdk_leaderboard)
    drivers = mock_irsdk_leaderboard.get_value("DriverInfo")["Drivers"]

    NEGATIVE_TO_NONE = -9.9

    ctx = LeaderboardContext(
        drivers=drivers,
        positions=[1],
        class_positions=[0],
        last_lap_times=[80],
        laps_started=[1],
        lap_dist_pct=[NEGATIVE_TO_NONE],
        is_pitroad=[False],
        multiclass=False,
    )

    result = builder.build(0, ctx)
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

    ctx = LeaderboardContext(
        drivers=drivers,
        positions=[1],
        class_positions=[1],
        last_lap_times=[80.0],
        laps_started=[5],
        lap_dist_pct=[0.3],
        is_pitroad=[False],
        multiclass=False,
    )

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
    assert result["lap_dist_pct"] == 0.3


# --- Leaderboard tests ---


def test_get_session_time_formats(mock_irsdk_leaderboard):
    leaderboard = Leaderboard(mock_irsdk_leaderboard)
    current_session = {"SessionType": "RACE", "SessionLaps": 10}
    player_lap_time = 80.0
    session_time_total = 123.0

    result_unformatted = leaderboard.get_session_time(
        current_session,
        player_lap_time,
        session_time_total,
        format=False,
    )
    assert isinstance(result_unformatted, float)

    result_formatted = leaderboard.get_session_time(
        current_session, player_lap_time, session_time_total, format=True
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
    assert result == {"message": "Iracing is not started."}


def test_get_neighbors_returns_expected(mock_irsdk_leaderboard):
    leaderboard = Leaderboard(mock_irsdk_leaderboard)
    
    drivers = mock_irsdk_leaderboard.get_value("DriverInfo")["Drivers"]
    lap_dist_pct = mock_irsdk_leaderboard.get_value("CarIdxLapDistPct")
    laps_started = mock_irsdk_leaderboard.get_value("CarIdxLap")
    is_pitroad = mock_irsdk_leaderboard.get_value("CarIdxOnPitRoad")
    
    ctx = LeaderboardContext(
        drivers=drivers,
        positions=mock_irsdk_leaderboard.get_value("CarIdxPosition"),
        class_positions=mock_irsdk_leaderboard.get_value("CarIdxClassPosition"),
        last_lap_times=mock_irsdk_leaderboard.get_value("CarIdxLastLapTime"),
        laps_started=laps_started,
        lap_dist_pct=lap_dist_pct,
        is_pitroad=is_pitroad,
        multiclass=False,
    )
    
    neighbors = leaderboard.neighbors.get_neighbors(
        player_idx=0,
        ctx=ctx,
    )

    assert "ahead" in neighbors
    assert "behind" in neighbors
    assert isinstance(neighbors["ahead"], list)
    assert isinstance(neighbors["behind"], list)


def test_get_session_info_returns_expected(mock_irsdk_leaderboard):
    leaderboard = Leaderboard(mock_irsdk_leaderboard)
    
    drivers = mock_irsdk_leaderboard.get_value("DriverInfo")["Drivers"]
    lap_dist_pct = mock_irsdk_leaderboard.get_value("CarIdxLapDistPct")
    laps_started = mock_irsdk_leaderboard.get_value("CarIdxLap")
    is_pitroad = mock_irsdk_leaderboard.get_value("CarIdxOnPitRoad")
    
    ctx = LeaderboardContext(
        drivers=drivers,
        positions=mock_irsdk_leaderboard.get_value("CarIdxPosition"),
        class_positions=mock_irsdk_leaderboard.get_value("CarIdxClassPosition"),
        last_lap_times=mock_irsdk_leaderboard.get_value("CarIdxLastLapTime"),
        laps_started=laps_started,
        lap_dist_pct=lap_dist_pct,
        is_pitroad=is_pitroad,
        multiclass=False,
    )
    
    data = leaderboard.get_session_info(player_idx=0, ctx=ctx)
    
    assert data["session_laps"] == 10
    assert data["session_time"] == 111.0
    assert data["player_lap_time"] == 11.1


def test_get_car_lap_time_returns_fastest_or_est(mock_irsdk_leaderboard):
    ctx = LeaderboardContext(
        drivers=mock_irsdk_leaderboard.get_value("DriverInfo")["Drivers"],
        positions=mock_irsdk_leaderboard.get_value("CarIdxPosition"),
        class_positions=[],
        last_lap_times=mock_irsdk_leaderboard.get_value("CarIdxLastLapTime"),
        laps_started=[],
        lap_dist_pct=[],
        is_pitroad=[],
        multiclass=False,
    )

    lb = Leaderboard(mock_irsdk_leaderboard)

    assert lb.get_car_lap_time(0, ctx) == 11.1
    assert lb.get_car_lap_time(1, ctx) == 22.2
    assert lb.get_car_lap_time(2, ctx) == 80.0


def test_get_last_pit_lap_behavior(mock_irsdk_leaderboard):
    builder = CarDataBuilder(mock_irsdk_leaderboard)
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
