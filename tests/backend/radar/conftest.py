import pytest

from backend.services.radar.service import RadarContext, RadarService


@pytest.fixture
def mock_service(mock_values) -> RadarService:
    """
    Returns the RadarService initialized with mock values.
    """
    return RadarService(mock_values)


@pytest.fixture
def mock_ctx(mock_values: dict) -> RadarContext:
    """
    Returns the RadarContext with mocked data from mock_values fixture.
    """
    defaults = {
        "dist_ahead": mock_values.get_value("CarDistAhead"),
        "dist_behind": mock_values.get_value("CarDistBehind"),
        "car_left_right": mock_values.get_value("CarLeftRight"),
    }

    def _make_ctx(**overrides):
        data = {**defaults, **overrides}
        return RadarContext(**data)

    return _make_ctx


@pytest.fixture
def mock_values(irsdk_mock_factory) -> dict:
    """
    Return dictionary containing the data
    required for testing the RadarService.
    """
    values = {
        "WeekendInfo": {"TrackLength": "1000 m"},
        "CarDistAhead": 5.0,
        "CarDistBehind": 6.0,
        "CarLeftRight": 0,
    }
    return irsdk_mock_factory(values)
