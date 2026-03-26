from unittest.mock import patch

from backend.services.track_map.service import TrackMapService


# --- Positive tests ---


def test_get_snapshot_returns_expected_structure(mock_service):
    snapshot = mock_service.get_snapshot()

    assert snapshot["status"] == "ok"
    assert snapshot["player_id"] == 0
    assert snapshot["is_session_changed"] is False
    assert len(snapshot["cars"]) == 2


def test_is_session_changed_returns_true_on_session_update(mock_values):
    service1 = TrackMapService(mock_values)
    service1.get_snapshot()

    # Changed SessionID value to get trigger
    new_values = mock_values.copy()
    new_values["WeekendInfo"]["SessionID"] = 999999999
    service2 = TrackMapService(new_values)

    snapshot = service2.get_snapshot()
    assert snapshot["is_session_changed"] is True


def test_build_context_multiclass_flag(irsdk_mock_factory):
    values = {
        "DriverInfo": {
            "Drivers": [
                {"CarClassID": 1},
                {"CarClassID": 2},
            ]
        },
    }
    service = TrackMapService(irsdk_mock_factory(values))
    ctx = service._build_context()
    assert ctx is not None
    assert ctx.multiclass is True


def test_track_svg_is_reused_from_cache_between_snapshots(mock_service):
    update_calls: list[tuple[int, str, str]] = []

    def fake_update(track_id, track_name, track_short_name):
        update_calls.append((track_id, track_name, track_short_name))
        mock_service._cached_track_svg = "<svg>track</svg>"
        mock_service._cached_start_finish_svg = "<svg>sf</svg>"
        mock_service._cached_track_id = track_id

    mock_service._update_track_svgs = fake_update

    first_snapshot = mock_service.get_snapshot()
    second_snapshot = mock_service.get_snapshot()

    assert len(update_calls) == 1
    assert first_snapshot["track_svg"] == "<svg>track</svg>"
    assert second_snapshot["track_svg"] == "<svg>track</svg>"
    assert first_snapshot["start_finish_svg"] == "<svg>sf</svg>"
    assert second_snapshot["start_finish_svg"] == "<svg>sf</svg>"


def test_track_svg_cache_is_refreshed_after_track_change(irsdk_mock_factory):
    values = {
        "PlayerCarIdx": 0,
        "SessionNum": 0,
        "CarIdxOnPitRoad": [False, False],
        "CarIdxLapDistPct": [0.3, 0.2],
        "CarIdxPosition": [1, 2],
        "CarIdxClassPosition": [0, 1],
        "DriverInfo": {
            "Drivers": [
                {
                    "CarNumber": "12",
                    "CarClassColor": 16711680,
                    "CarClassID": 1,
                },
                {
                    "CarNumber": "8",
                    "CarClassColor": 16711680,
                    "CarClassID": 1,
                },
            ]
        },
        "WeekendInfo": {
            "SessionID": 1234567890,
            "TrackID": 123,
            "TrackName": "Test Track",
            "TrackDisplayShortName": "test_track",
        },
    }
    irsdk_mock = irsdk_mock_factory(values)
    service = TrackMapService(irsdk_mock)

    update_calls: list[int] = []

    def fake_update(track_id, track_name, track_short_name):
        update_calls.append(track_id)
        service._cached_track_svg = f"<svg>{track_id}</svg>"
        service._cached_start_finish_svg = f"<svg>sf-{track_id}</svg>"
        service._cached_track_id = track_id

    service._update_track_svgs = fake_update

    first_snapshot = service.get_snapshot()
    values["WeekendInfo"]["TrackID"] = 456
    values["WeekendInfo"]["TrackName"] = "Second Track"
    values["WeekendInfo"]["TrackDisplayShortName"] = "second_track"
    second_snapshot = service.get_snapshot()

    assert update_calls == [123, 456]
    assert first_snapshot["track_svg"] == "<svg>123</svg>"
    assert second_snapshot["track_svg"] == "<svg>456</svg>"


# --- Negative tests ---


def test_build_context_returns_none_when_no_drivers(irsdk_mock_factory):
    values = {
        "DriverInfo": {"Drivers": []},
        "CarIdxLapDistPct": [],
        "CarIdxOnPitRoad": [],
        "CarIdxPosition": [],
        "CarIdxClassPosition": [],
    }
    service = TrackMapService(irsdk_mock_factory(values))
    ctx = service._build_context()
    assert ctx is None
