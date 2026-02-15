import pytest

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
    Returns the TrackMapCarBuilder initialized.
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


@pytest.fixture
def mock_values(irsdk_mock_factory) -> dict:
    """
    Return dictionary containing the data
    required for testing the TrackMapService.
    """
    values = {
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
        }
    }
    return irsdk_mock_factory(values)
