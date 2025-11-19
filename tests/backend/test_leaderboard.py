import pytest
from unittest.mock import MagicMock
import time

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
    assert TimeFormatter.format(seconds) == expected


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
        0, drivers, [1], [1], [80.0], [5], [0.3], multiclass=False
    )
    assert result is None


def test_get_starting_position_from_qualify_stats(mock_irsdk_leaderboard):
    builder = CarDataBuilder(mock_irsdk_leaderboard)
    pos = builder._get_starting_position(car_idx=1, field="Position", offset=0)
    assert pos == 2


def test_get_starting_position_missing_qualify(mock_irsdk_leaderboard):
    builder = CarDataBuilder(mock_irsdk_leaderboard)
    pos = builder._get_starting_position(car_idx=999, field="Position", offset=0)
    assert pos == 0


def test_starting_position_falls_back_to_race(mock_irsdk_leaderboard):
    builder = CarDataBuilder(mock_irsdk_leaderboard)

    qualify_results = (
        mock_irsdk_leaderboard.get_value("SessionInfo")["Sessions"][0]["ResultsPositions"]
    )
    assert not any(r["CarIdx"] == 2 for r in qualify_results)

    positions = mock_irsdk_leaderboard.get_value("CarIdxPosition")
    drivers = mock_irsdk_leaderboard.get_value("DriverInfo")["Drivers"]
    result = builder.build(
        idx=2,
        drivers=drivers,
        positions=positions,
        class_positions=[0, 1, 2],
        last_lap_times=[80.0, 81.0, 82.0],
        laps_started=[5, 4, 3],
        lap_dist_pct=[0.1, 0.2, 0.3],
        multiclass=False,
    )
    assert result["pos"] == 3


def test_builder_converts_minus_one_position_to_none(mock_irsdk_leaderboard):
    builder = CarDataBuilder(mock_irsdk_leaderboard)
    drivers = mock_irsdk_leaderboard.get_value("DriverInfo")["Drivers"]

    result = builder.build(
        1,
        drivers,
        positions=[1, -1, 3],
        class_positions=[0, -1, 2],
        last_lap_times=[80, 81, 82],
        laps_started=[5, 5, 5],
        lap_dist_pct=[0.3, 0.2, 0.2],
        multiclass=False,
    )
    assert result["pos"] is None


def test_builder_negative_laps_converted_to_zero(mock_irsdk_leaderboard):
    builder = CarDataBuilder(mock_irsdk_leaderboard)
    drivers = mock_irsdk_leaderboard.get_value("DriverInfo")["Drivers"]
    result = builder.build(
        0,
        drivers,
        [1], [0], [80], [-999], [0.5],
        multiclass=False
    )
    assert result["laps_started"] == 0


def test_builder_lap_dist_pct_negative_becomes_none(mock_irsdk_leaderboard):
    builder = CarDataBuilder(mock_irsdk_leaderboard)
    drivers = mock_irsdk_leaderboard.get_value("DriverInfo")["Drivers"]
    result = builder.build(
        0,
        drivers,
        [1], [0], [80], [1], [-0.5],
        multiclass=False
    )
    assert result["lap_dist_pct"] == None


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
        0, drivers, [1], [1], [80.0], [5], [0.3], multiclass=False
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
    irsdk.get_value.side_effect = lambda key: {"DriverInfo": {"Drivers": []}}.get(key)
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
