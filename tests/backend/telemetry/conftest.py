import pytest

from backend.services.telemetry.service import (
    TelemetryContext,
    TelemetryService,
)


@pytest.fixture
def mock_service(mock_values) -> TelemetryService:
    """
    Returns the TelemetryService initialized with mock values.
    """
    return TelemetryService(mock_values)


@pytest.fixture
def mock_ctx(mock_values) -> TelemetryContext:
    """
    Returns the TelemetryContext with mocked data from mock_values fixture.
    """
    defaults = {
        "throttle": mock_values.get_value("Throttle"),
        "brake": mock_values.get_value("Brake"),
        "gear": mock_values.get_value("Gear"),
        "speed_km": mock_values.get_speed_kmh(),
    }

    def _make_ctx(**overrides):
        data = {**defaults, **overrides}
        return TelemetryContext(**data)

    return _make_ctx


@pytest.fixture
def mock_values(irsdk_mock_factory) -> dict:
    """
    Return dictionary containing the data
    required for testing the TelemetryService.
    """
    values = {
        "Throttle": 0.73,
        "Brake": 0.11,
        "Gear": 4,
    }
    irsdk = irsdk_mock_factory(values)
    irsdk.get_speed_kmh = lambda: 246.8
    return irsdk
