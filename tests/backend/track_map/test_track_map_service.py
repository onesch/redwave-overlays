from backend.services.track_map.service import TrackMapService


# --- Positive tests ---


def test_get_snapshot_returns_expected_structure(mock_service):
    snapshot = mock_service.get_snapshot()

    assert snapshot["status"] == "ok"
    assert snapshot["player_id"] == 0
    assert snapshot["is_session_changed"] is False
    assert len(snapshot["cars"]) == 2


def test_is_session_changed_returns_true_on_session_update(
    irsdk_mock_factory,
):
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

    service1 = TrackMapService(irsdk_mock_factory(values))
    service1.get_snapshot()

    values["WeekendInfo"]["SessionID"] = 999999999

    service2 = TrackMapService(irsdk_mock_factory(values))

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


def test_build_context_ignores_pace_car_class(irsdk_mock_factory):
    values = {
        "DriverInfo": {
            "Drivers": [
                {"UserName": "Driver1", "CarClassID": 5},
                {"UserName": "Driver2", "CarClassID": 5},
                {"UserName": "Pace Car", "CarClassID": 11, "CarIsPaceCar": 1},
            ]
        },
    }
    service = TrackMapService(irsdk_mock_factory(values))
    ctx = service._build_context()
    assert ctx.multiclass is False


def test_snapshot_cars_contain_class_data(mock_service):
    car = mock_service.get_snapshot()["cars"][0]

    assert car["class_id"] == 1
    assert car["color"] == "#ff0000"


def test_snapshot_contains_multiclass_and_track(mock_service):
    snapshot = mock_service.get_snapshot()

    assert snapshot["multiclass"] is False
    assert snapshot["track"]["id"] == 123
    assert snapshot["track"]["start_finish"] == {"pct": 0.5, "direction": 1}
    assert len(snapshot["track"]["points"]) == 3


def test_track_is_fetched_once_for_the_same_track(mock_service, fake_fetch):
    first = mock_service.get_snapshot()
    second = mock_service.get_snapshot()

    assert fake_fetch.calls == [123]
    assert first["track"] == second["track"]


def test_track_is_fetched_again_after_track_change(
    mock_values, mock_values_dict, fake_fetch
):
    service = TrackMapService(mock_values)

    service.get_snapshot()
    mock_values_dict["WeekendInfo"]["TrackID"] = 456
    snapshot = service.get_snapshot()

    assert fake_fetch.calls == [123, 456]
    assert snapshot["track"]["id"] == 456


def test_track_is_loaded_from_disk_cache_after_restart(
    mock_values, fake_fetch, user_data_dir
):
    TrackMapService(mock_values).get_snapshot()

    # A new service instance simulates an app restart: the geometry comes
    # from the cache file, without a new API request.
    snapshot = TrackMapService(mock_values).get_snapshot()

    assert fake_fetch.calls == [123]
    assert snapshot["track"]["id"] == 123
    assert (user_data_dir / "track_geometry_cache.json.gz").exists()


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


def test_failed_fetch_returns_no_track_and_is_not_cached(
    mock_values, fake_fetch, user_data_dir
):
    fake_fetch.geometry = None

    snapshot = TrackMapService(mock_values).get_snapshot()

    assert snapshot["track"] is None
    assert not (user_data_dir / "track_geometry_cache.json.gz").exists()

    # After a restart the track is requested again, not taken from the cache.
    TrackMapService(mock_values).get_snapshot()
    assert fake_fetch.calls == [123, 123]


def test_missing_track_id_skips_fetch(mock_values, mock_values_dict, fake_fetch):
    mock_values_dict["WeekendInfo"]["TrackID"] = None
    service = TrackMapService(mock_values)

    snapshot = service.get_snapshot()

    assert snapshot["track"] is None
    assert fake_fetch.calls == []

    # The real track id arriving later is still loaded.
    mock_values_dict["WeekendInfo"]["TrackID"] = 123
    assert service.get_snapshot()["track"]["id"] == 123
