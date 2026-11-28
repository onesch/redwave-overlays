import pytest
from unittest.mock import MagicMock

from backend.components.car_class import CarClassComponent
from backend.components.track_position import CarPositionContext
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


def test_is_multiclass_returns_false_for_single_class(mock_ctx):
    ctx = mock_ctx(drivers=[{"CarClassID": 1}, {"CarClassID": 1}])
    assert CarClassComponent.is_multiclass(ctx.drivers) is False


def test_is_multiclass_returns_true_for_multiple_classes(mock_ctx):
    ctx = mock_ctx(drivers=[{"CarClassID": 1}, {"CarClassID": 2}])
    assert CarClassComponent.is_multiclass(ctx.drivers) is True


def test_reset_pit_stops_calls_reset_on_new_session(mock_service):
    mock_service._last_session_num = 1
    mock_service._last_session_time = 100.0
    session_info = {"CurrentSessionNum": 2}
    mock_service.pit_stops.clear = MagicMock()

    mock_service._reset_pit_stops(session_info, session_time=200.0)

    mock_service.pit_stops.clear.assert_called_once()


def test_reset_pit_stops_does_not_call_reset_on_same_session(mock_service):
    mock_service._last_session_num = 2
    mock_service._last_session_time = 100.0
    session_info = {"CurrentSessionNum": 2}
    mock_service.pit_stops.clear = MagicMock()

    mock_service._reset_pit_stops(session_info, session_time=101.0)

    mock_service.pit_stops.clear.assert_not_called()


def test_reset_pit_stops_resets_on_same_session_restart(mock_service):
    mock_service._last_session_num = 2
    mock_service._last_session_time = 1200.0
    session_info = {"CurrentSessionNum": 2}
    mock_service.pit_stops.clear = MagicMock()

    mock_service._reset_pit_stops(session_info, session_time=0.0)

    mock_service.pit_stops.clear.assert_called_once()
    assert mock_service._last_session_time == 0.0


def test_build_context_collects_pit_labels_of_the_snapshot(mock_values, monkeypatch):
    irsdk = mock_values()
    read = irsdk.get_value.side_effect
    irsdk.get_value.side_effect = lambda key: (
        [False, True, False] if key == "CarIdxOnPitRoad" else read(key)
    )
    monkeypatch.setattr(
        "backend.services.leaderboard.service.time.time", lambda: 1000.0
    )
    lb = Leaderboard(irsdk)

    ctx = lb._build_context()

    # Car 1 is on the pit road on lap 5 (CarIdxLap).
    assert ctx.pit_labels == {1: "IN L5"}


def test_build_context_clears_pit_stops_of_the_previous_session(mock_service):
    mock_service.pit_stops.update(laps_started=[3], is_pitroad=[True], now=0.0)
    # The mocked SessionInfo is on CurrentSessionNum 1.
    mock_service._last_session_num = 0

    ctx = mock_service._build_context()

    assert ctx.pit_labels == {}


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
    assert ctx.radio_transmit_car_idx == -1
    assert ctx.player_idx == 0


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


def test_build_context_calculates_lap_deltas_from_player(mock_service):
    # CarIdxLap [5, 5, 4], CarIdxLapDistPct [0.6, 0.3, 0.9], player 0:
    # car 1 is on the same lap, car 2 is a lap behind.
    ctx = mock_service._build_context()

    assert ctx.lap_deltas == {1: 0, 2: -1}


def test_build_context_collects_car_positions_once_per_snapshot(mock_service):
    ctx = mock_service._build_context()

    assert ctx.car_positions == Leaderboard.build_car_positions(
        drivers=ctx.drivers,
        lap_dist_pct=ctx.lap_dist_pct,
        est_times=ctx.est_times,
    )
    assert set(ctx.car_positions) == set(range(len(ctx.drivers)))


def test_build_car_positions_takes_values_by_car_index():
    positions = Leaderboard.build_car_positions(
        drivers=[
            {"CarClassID": 4074, "CarClassEstLapTime": 230.72},
            {"CarClassID": 4074, "CarClassEstLapTime": 232.76},
            # No telemetry for this car yet.
            {"CarClassID": 2523, "CarClassEstLapTime": 211.4},
        ],
        lap_dist_pct=[0.5, 0.62],
        est_times=[115.36, 144.31],
    )

    assert positions == {
        0: CarPositionContext(0.5, 115.36, 230.72, 4074),
        1: CarPositionContext(0.62, 144.31, 232.76, 4074),
    }


def test_build_snapshot_includes_cached_irating_deltas(mock_service, mock_ctx):
    ctx = mock_ctx(irating_deltas={101: 60, 102: 2, 103: -60})

    snapshot = mock_service._build_snapshot(ctx)

    assert snapshot["irating_deltas"] == {101: 60, 102: 2, 103: -60}


def test_build_snapshot_uses_player_idx_from_context(mock_service, mock_ctx):
    # The SDK reports PlayerCarIdx 0: the snapshot must follow the context.
    ctx = mock_ctx(player_idx=1)

    snapshot = mock_service._build_snapshot(ctx)

    assert snapshot["player"]["car_idx"] == 1
    assert 1 not in [car["car_idx"] for car in snapshot["cars"]]


def test_get_snapshot_reads_player_car_idx_once(mock_values):
    irsdk = mock_values()

    Leaderboard(irsdk).get_snapshot()

    reads = [
        call
        for call in irsdk.get_value.call_args_list
        if call.args == ("PlayerCarIdx",)
    ]
    assert len(reads) == 1


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


# --- track time line ---


class RecordingTimeLine:
    """Records what Leaderboard records into the player's time line."""

    def __init__(self):
        self.bindings = []
        self.samples = []

    def bind(self, track_id, class_id, est_lap_time):
        self.bindings.append((track_id, class_id, est_lap_time))

    def record(self, car):
        self.samples.append((car.lap_dist_pct, car.est_time, car.est_lap_time))


def test_track_time_line_records_player_class_cars_off_pit_road(
    mock_service,
    mock_ctx,
):
    mock_service.track_time_line = RecordingTimeLine()
    ctx = mock_ctx(
        drivers=[
            {"CarClassID": 1, "CarClassEstLapTime": 100.0},
            {"CarClassID": 2},
            # Another car model of the player's class.
            {"CarClassID": 1, "CarClassEstLapTime": 102.0},
            {"CarClassID": 1},
            {"CarClassID": 1, "UserName": "Pace Car", "CarIsPaceCar": 1},
        ],
        lap_dist_pct=[0.1, 0.2, 0.3, 0.4, 0.5],
        est_times=[10.0, 20.0, 30.0, 40.0, 50.0],
        is_pitroad=[False, False, False, True, False],
        player_idx=0,
    )

    mock_service._record_track_time_line(ctx)

    # Another class, pit road and the pace car are left out; every sample
    # comes with its car's reference lap for rescaling.
    assert mock_service.track_time_line.samples == [
        (0.1, 10.0, 100.0),
        (0.3, 30.0, 102.0),
    ]


def test_track_time_line_is_bound_to_track_class_and_player_lap_time(
    mock_service,
    mock_ctx,
):
    mock_service.track_time_line = RecordingTimeLine()
    mock_service.irsdk.get_value = lambda key: (
        {"TrackID": 123} if key == "WeekendInfo" else None
    )
    ctx = mock_ctx(
        drivers=[{"CarClassID": 1, "CarClassEstLapTime": 100.0}],
        lap_dist_pct=[0.1],
        est_times=[10.0],
        is_pitroad=[False],
        player_idx=0,
    )

    mock_service._record_track_time_line(ctx)

    assert mock_service.track_time_line.bindings == [(123, 1, 100.0)]


def test_track_time_line_is_not_recorded_without_player(mock_service, mock_ctx):
    mock_service.track_time_line = RecordingTimeLine()

    mock_service._record_track_time_line(mock_ctx(player_idx=None))

    assert mock_service.track_time_line.samples == []


def test_build_context_keeps_one_track_time_line_across_snapshots(mock_service):
    first = mock_service._build_context()
    second = mock_service._build_context()

    assert first.track_time_line is mock_service.track_time_line
    assert second.track_time_line is mock_service.track_time_line
