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
