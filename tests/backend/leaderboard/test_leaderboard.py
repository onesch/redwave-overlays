import pytest
from unittest.mock import MagicMock
import time

from backend.services.leaderboard.service import Leaderboard


def test_get_session_info_returns_expected(
    mock_irsdk_leaderboard, ctx_from_mock
):
    lb = Leaderboard(mock_irsdk_leaderboard)
    data = lb.get_session_info(player_idx=0, ctx=ctx_from_mock)
    assert data["session_laps"] == 10
    assert data["player_lap_time"] == 11.1


def test_get_car_lap_time_returns_fastest_or_est(
    mock_irsdk_leaderboard, ctx_from_mock
):
    ctx = ctx_from_mock()
    lb = Leaderboard(mock_irsdk_leaderboard)
    assert lb.get_car_lap_time(0, ctx) == 11.1
    assert lb.get_car_lap_time(1, ctx) == 22.2
    assert lb.get_car_lap_time(2, ctx) == 80.0


def test_get_session_time_formats(leaderboard):
    current_session = {"SessionType": "RACE", "SessionLaps": 10}
    player_lap_time = 80.0
    session_time_total = 123.0

    unformatted = leaderboard.get_session_time(
        current_session,
        player_lap_time,
        session_time_total,
        format=False,
    )
    formatted = leaderboard.get_session_time(
        current_session,
        player_lap_time,
        session_time_total,
        format=True,
    )

    assert isinstance(unformatted, float)
    assert isinstance(formatted, str)
    assert formatted.startswith("~")
    assert formatted.endswith("m")


def test_leaderboard_snapshot_structure(leaderboard):
    snapshot = leaderboard.get_leaderboard_snapshot()
    keys = (
        "cars",
        "player",
        "neighbors",
        "leaderboard_data",
        "multiclass",
        "timestamp",
    )

    assert all(k in snapshot for k in keys)
    assert isinstance(snapshot["timestamp"], int)


def test_leaderboard_snapshot_multiclass(mock_irsdk_leaderboard_multiclass):
    lb = Leaderboard(mock_irsdk_leaderboard_multiclass)
    snapshot = lb.get_leaderboard_snapshot()
    assert snapshot["multiclass"] is True


def test_leaderboard_no_drivers_returns_error(irsdk_mock_factory):
    irsdk = irsdk_mock_factory({"DriverInfo": {"Drivers": []}})
    leaderboard = Leaderboard(irsdk)

    result = leaderboard.get_leaderboard_snapshot()
    assert result == {
        "status": "waiting",
        "player": None,
        "cars": [],
        "neighbors": {"ahead": [], "behind": []},
        "leaderboard_data": None,
        "multiclass": False,
        "timestamp": int(time.time()),
    }


def test_is_multiclass_returns_false_for_single_class(
    leaderboard, ctx_from_mock
):
    ctx = ctx_from_mock(drivers=[{"CarClassID": 1}, {"CarClassID": 1}])
    assert leaderboard._is_multiclass(ctx.drivers) is False


def test_is_multiclass_returns_true_for_multiple_classes(
    leaderboard, ctx_from_mock
):
    ctx = ctx_from_mock(drivers=[{"CarClassID": 1}, {"CarClassID": 2}])
    assert leaderboard._is_multiclass(ctx.drivers) is True


def test_get_estimated_lap_time_invalid_values(leaderboard, ctx_from_mock):
    ctx = ctx_from_mock(
        drivers=[{"CarClassEstLapTime": -5}, {"CarClassEstLapTime": "abc"}]
    )
    assert leaderboard._get_estimated_lap_time(0, ctx) is None
    assert leaderboard._get_estimated_lap_time(1, ctx) is None


def test_get_best_lap_time_invalid_values(
    mock_irsdk_leaderboard, ctx_from_mock
):
    mock_irsdk_leaderboard.get_value = lambda key: [0, "abc", None]
    leaderboard = Leaderboard(mock_irsdk_leaderboard)
    ctx = ctx_from_mock()
    assert leaderboard._get_best_lap_time(0, ctx) is None
    assert leaderboard._get_best_lap_time(1, ctx) is None
    assert leaderboard._get_best_lap_time(2, ctx) is None


def test_get_lap_session_time_unlimited(leaderboard):
    current_session = {"SessionLaps": "unlimited"}
    result = leaderboard._get_lap_session_time(
        current_session, player_lap_time=80
    )
    assert result is None


def test_reset_pit_status_calls_reset_on_new_session(
    leaderboard, mock_irsdk_leaderboard
):
    leaderboard._last_session_num = 1
    session_info = {"CurrentSessionNum": 2}
    leaderboard.builder.reset_pit_data = MagicMock()
    leaderboard._reset_pit_status(session_info)
    leaderboard.builder.reset_pit_data.assert_called_once()


def test_reset_pit_status_does_not_call_reset_on_same_session(
    leaderboard, mock_irsdk_leaderboard
):
    leaderboard._last_session_num = 2
    session_info = {"CurrentSessionNum": 2}
    leaderboard.builder.reset_pit_data = MagicMock()
    leaderboard._reset_pit_status(session_info)
    leaderboard.builder.reset_pit_data.assert_not_called()


def test_get_current_session_empty_or_out_of_bounds(leaderboard):
    assert (
        leaderboard._get_current_session(
            {"Sessions": [], "CurrentSessionNum": 0}
        )
        == {}
    )
    assert (
        leaderboard._get_current_session(
            {"Sessions": [{}], "CurrentSessionNum": 2}
        )
        == {}
    )
