import pytest
from unittest.mock import MagicMock

from backend.services.leaderboard.context import LeaderboardContext
from backend.services.leaderboard.service import Leaderboard


def test_get_session_info_returns_expected(mock_values, mock_ctx):
    lb = Leaderboard(mock_values())
    data = lb.get_session_info(player_idx=0, ctx=mock_ctx())
    assert data["session_laps"] == 10
    assert data["player_lap_time"] == pytest.approx(11.1)


def test_get_session_time_formats(mock_service):
    current_session = {"SessionType": "Race", "SessionLaps": 10}
    player_lap_time = 80.0

    unformatted = mock_service.get_session_time(
        current_session,
        player_lap_time,
        is_format=False,
    )
    formatted = mock_service.get_session_time(
        current_session,
        player_lap_time,
        is_format=True,
    )

    assert isinstance(unformatted, float)
    assert isinstance(formatted, str)
    assert formatted.startswith("~")
    assert formatted.endswith("m")


def test_leaderboard_snapshot_structure(mock_service):
    snapshot = mock_service.get_snapshot()
    keys = (
        "cars",
        "player",
        "neighbors",
        "leaderboard_data",
        "multiclass",
    )

    assert all(k in snapshot for k in keys)


def test_leaderboard_snapshot_multiclass(mock_values):
    lb = Leaderboard(mock_values(is_multiclass=True))
    snapshot = lb.get_snapshot()
    assert snapshot["multiclass"] is True


def test_leaderboard_no_drivers_returns_error(irsdk_mock_factory):
    irsdk = irsdk_mock_factory({"DriverInfo": {"Drivers": []}})
    mock_service = Leaderboard(irsdk)

    result = mock_service.get_snapshot()

    assert result["status"] == "waiting"
    assert result["cars"] == []


def test_is_multiclass_returns_false_for_single_class(mock_service, mock_ctx):
    ctx = mock_ctx(drivers=[{"CarClassID": 1}, {"CarClassID": 1}])
    assert mock_service._is_multiclass(ctx.drivers) is False


def test_is_multiclass_returns_true_for_multiple_classes(
    mock_service, mock_ctx
):
    ctx = mock_ctx(drivers=[{"CarClassID": 1}, {"CarClassID": 2}])
    assert mock_service._is_multiclass(ctx.drivers) is True


def test_reset_pit_status_calls_reset_on_new_session(mock_service):
    mock_service._last_session_num = 1
    session_info = {"CurrentSessionNum": 2}
    mock_service.builder.reset_pit_data = MagicMock()
    mock_service._reset_pit_status(session_info)
    mock_service.builder.reset_pit_data.assert_called_once()


def test_reset_pit_status_does_not_call_reset_on_same_session(mock_service):
    mock_service._last_session_num = 2
    session_info = {"CurrentSessionNum": 2}
    mock_service.builder.reset_pit_data = MagicMock()
    mock_service._reset_pit_status(session_info)
    mock_service.builder.reset_pit_data.assert_not_called()


def test_get_current_session_empty_or_out_of_bounds(mock_service):
    assert (
        mock_service._get_current_session({"Sessions": [], "CurrentSessionNum": 0})
        == {}
    )
    assert (
        mock_service._get_current_session({"Sessions": [{}], "CurrentSessionNum": 2})
        == {}
    )


def test_empty_snapshot_structure(mock_service):
    snapshot = mock_service._empty_snapshot()

    assert isinstance(snapshot, dict)

    assert snapshot["status"] == "waiting"
    assert snapshot["cars"] == []


def test_build_context_success(mock_service):
    ctx = mock_service._build_context()

    assert isinstance(ctx, LeaderboardContext)

    assert len(ctx.drivers) == 3
    assert ctx.positions == [1, 2, 3]
    assert ctx.class_positions == [0, 1, 2]
    assert ctx.last_lap_times == [80.0, 81.5, 82.2]
    assert ctx.lap_dist_pct == [0.6, 0.3, 0.9]
    assert ctx.is_pitroad == [False, False, False]
    assert ctx.laps_started == [5, 5, 4]
    assert ctx.session_fastest_lap == pytest.approx(11.1)
    assert ctx.class_fastest_laps == {1: pytest.approx(11.1)}
    assert ctx.multiclass is False


def test_build_context_multiclass(mock_values):
    mock_service = Leaderboard(mock_values(is_multiclass=True))
    ctx = mock_service._build_context()

    assert isinstance(ctx, LeaderboardContext)
    assert ctx.class_fastest_laps == {
        1: pytest.approx(11.1),
        2: pytest.approx(22.2),
    }
    assert ctx.multiclass is True


def test_build_context_returns_none_when_no_drivers(irsdk_mock_factory):
    irsdk = irsdk_mock_factory(
        {
            "DriverInfo": {"Drivers": []},
        }
    )

    mock_service = Leaderboard(irsdk)
    ctx = mock_service._build_context()

    assert ctx is None


@pytest.mark.parametrize(
    "raw_laps,expected",
    [
        ([-1], [0]),
        ([1], [1]),
        ([0], [0]),
        ([None], [0]),
        (["str"], [0]),
    ],
)
def test_normalize_laps_started(mock_service, raw_laps, expected):
    assert mock_service._normalize_laps_started(raw_laps) == expected
