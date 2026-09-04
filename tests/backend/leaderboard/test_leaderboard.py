import pytest
from unittest.mock import MagicMock

from backend.services.leaderboard.context import LeaderboardContext
from backend.services.leaderboard.service import Leaderboard


def test_get_session_info_returns_expected(mock_values, mock_ctx):
    lb = Leaderboard(mock_values())
    data = lb.get_session_info(player_idx=0, ctx=mock_ctx())
    assert data["session_laps"] == 10
    assert data["player_lap_time"] == pytest.approx(11.1)


def test_get_session_time_returns_lap_based(mock_service):
    current_session = {"SessionType": "Race", "SessionLaps": 10}
    player_lap_time = 80.0

    session_time, is_approximate = mock_service.get_session_time(
        current_session, player_lap_time,
    )

    assert isinstance(session_time, float)
    assert is_approximate is True


def test_get_session_time_falls_back_to_total(mock_service):
    current_session = {"SessionType": "Race", "SessionLaps": "unlimited"}
    player_lap_time = 80.0

    session_time, is_approximate = mock_service.get_session_time(
        current_session, player_lap_time,
    )

    assert session_time == mock_service.irsdk.get_value("SessionTimeTotal")
    assert is_approximate is False


def test_leaderboard_snapshot_structure(mock_service):
    snapshot = mock_service.get_snapshot()
    keys = (
        "cars",
        "player",
        "neighbors",
        "leaderboard_data",
        "multiclass",
        "irating_deltas",
    )

    assert all(k in snapshot for k in keys)
    assert "sof" in snapshot["leaderboard_data"]


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
    assert ctx.sof == 1829
    assert ctx.starting_positions == {0: 2, 1: 3, 2: 1}
    assert ctx.starting_class_positions == {0: 2, 1: 3, 2: 1}


def test_build_context_multiclass(mock_values):
    mock_service = Leaderboard(mock_values(is_multiclass=True))
    ctx = mock_service._build_context()

    assert isinstance(ctx, LeaderboardContext)
    assert ctx.class_fastest_laps == {
        1: pytest.approx(11.1),
        2: pytest.approx(22.2),
    }
    assert ctx.multiclass is True
    assert ctx.sof == 1845  # for class №1 from mock_values 101 and 103 ids.
    assert ctx.starting_positions == {0: 2, 1: 3, 2: 1}
    assert ctx.starting_class_positions == {0: 2, 1: 2, 2: 1}


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


def test_build_snapshot_includes_cached_irating_deltas(mock_service, mock_ctx):
    ctx = mock_ctx(irating_deltas={101: 60, 102: 2, 103: -60})

    snapshot = mock_service._build_snapshot(ctx)

    assert snapshot["irating_deltas"] == {101: 60, 102: 2, 103: -60}


def test_calculate_irating_deltas_uses_finishing_order_by_class(
    mock_service,
    mock_ctx,
):
    ctx = mock_ctx(
        drivers=[
            {
                "UserName": "Driver1",
                "UserID": 101,
                "IRating": 2000,
                "CarClassID": 1,
            },
            {
                "UserName": "Driver2",
                "UserID": 102,
                "IRating": 1800,
                "CarClassID": 2,
            },
            {
                "UserName": "Driver3",
                "UserID": 103,
                "IRating": 1700,
                "CarClassID": 1,
            },
            {
                "UserName": "Driver4",
                "UserID": 104,
                "IRating": 1600,
                "CarClassID": 2,
            },
        ],
        positions=[2, 1, 1, -1],
        class_positions=[2, 1, 1, -1],
        multiclass=True,
    )

    result = mock_service._calculate_irating_deltas(ctx)

    assert result == {103: 56, 101: -55, 102: 1}
    assert 104 not in result


def test_calculate_sof_returns_expected_value(
    mock_service,
    mock_ctx,
):
    ctx = mock_ctx(
        drivers=[
            {
                "UserID": 101,
                "IRating": 2000,
                "CarClassID": 1,
            },
            {
                "UserID": 102,
                "IRating": 1800,
                "CarClassID": 1,
            },
            {
                "UserID": 103,
                "IRating": 1700,
                "CarClassID": 1,
            },
        ],
        multiclass=False,
    )

    result = mock_service._calculate_sof(ctx, player_idx=0)

    expected = mock_service.irating_calculator.calculate_sof(
        {
            101: 2000,
            102: 1800,
            103: 1700,
        }
    )

    assert result == expected


def test_calculate_sof_uses_player_class_in_multiclass(
    mock_service,
    mock_ctx,
):
    ctx = mock_ctx(
        drivers=[
            {
                "UserID": 101,
                "IRating": 2000,
                "CarClassID": 1,
            },
            {
                "UserID": 102,
                "IRating": 1800,
                "CarClassID": 2,
            },
            {
                "UserID": 103,
                "IRating": 1700,
                "CarClassID": 1,
            },
        ],
        multiclass=True,
    )

    result = mock_service._calculate_sof(ctx, player_idx=0)

    expected = mock_service.irating_calculator.calculate_sof(
        {
            101: 2000,
            103: 1700,
        }
    )

    assert result == expected


def test_calculate_sof_includes_unstarted_drivers(
    mock_service,
    mock_ctx,
):
    ctx = mock_ctx(
        drivers=[
            {
                "UserID": 101,
                "IRating": 2000,
                "CarClassID": 1,
            },
            {
                "UserID": 102,
                "IRating": 1800,
                "CarClassID": 1,
            },
            {
                "UserID": 103,
                "IRating": 1700,
                "CarClassID": 1,
            },
        ],
        positions=[0, 0, 0],
        multiclass=False,
    )

    result = mock_service._calculate_sof(ctx, player_idx=0)

    expected = mock_service.irating_calculator.calculate_sof(
        {
            101: 2000,
            102: 1800,
            103: 1700,
        }
    )

    assert result == expected
