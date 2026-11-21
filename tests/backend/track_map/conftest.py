import pytest
from types import SimpleNamespace

from backend.services.track_map import service as track_map_service
from backend.services.track_map.service import (
    TrackMapCarBuilder,
    TrackMapService,
    TrackMapContext,
)


@pytest.fixture
def mock_service(mock_values: dict) -> TrackMapService:
    """
    Returns the TrackMapService initialized with mock values.
    """
    return TrackMapService(mock_values)


@pytest.fixture
def mock_builder() -> TrackMapCarBuilder:
    """
    Returns an initialized TrackMapCarBuilder object.
    """
    return TrackMapCarBuilder()


@pytest.fixture
def mock_ctx(mock_values: dict) -> TrackMapContext:
    """
    Returns the TrackMapContext with mocked data from mock_values fixture.
    """
    defaults = {
        "drivers": mock_values.get_value("DriverInfo")["Drivers"],
        "lap_dist_pct": mock_values.get_value("CarIdxLapDistPct"),
        "is_pitroad": mock_values.get_value("CarIdxOnPitRoad"),
        "positions": mock_values.get_value("CarIdxPosition"),
        "class_positions": mock_values.get_value(
            "CarIdxClassPosition"
        ),
        "multiclass": False,
    }

    def _make_ctx(**overrides):
        data = {**defaults, **overrides}
        return TrackMapContext(**data)

    return _make_ctx


@pytest.fixture(autouse=True)
def fake_fetch(monkeypatch) -> SimpleNamespace:
    """
    Replaces the Track Map API request so tests never hit the network.
    Records requested track ids in `calls`; set `geometry` to change
    the returned value (None simulates a failed request).
    """
    fake = SimpleNamespace(
        calls=[],
        geometry={
            "view_box": (0.0, 0.0, 1920.0, 1080.0),
            "points": [(0.0, 0.0), (10.0, 0.0), (0.0, 0.0)],
            "start_finish": {"pct": 0.5, "direction": 1},
        },
    )

    def _fetch(track_id):
        fake.calls.append(track_id)
        return fake.geometry

    monkeypatch.setattr(track_map_service, "fetch_track_geometry", _fetch)
    return fake


@pytest.fixture
def mock_values_dict() -> dict:
    """
    Return dictionary containing the data
    required for testing the TrackMapService.
    """
    return {
        "PlayerCarIdx": 0,
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
                }
            ]
        },
        "WeekendInfo": {
            "SessionID": 1234567890,
            "SessionNum": 0,
            "TrackID": 123,
        }
    }

@pytest.fixture
def mock_values(irsdk_mock_factory, mock_values_dict):
    """
    Returns the irsdk mock serving mock_values_dict.
    """
    return irsdk_mock_factory(mock_values_dict)
