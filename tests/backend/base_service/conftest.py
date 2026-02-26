import pytest

from backend.services.base import (
    BaseCarBuilder,
    BaseService,
    SessionStateContext,
)


@pytest.fixture
def mock_service(mock_builder, mock_irsdk_service) -> BaseService:
    """
    Returns an initialized BaseService object
    with real builder and mocked irsdk.
    """
    return BaseService(
        irsdk_service=mock_irsdk_service,
        builder=mock_builder,
    )


@pytest.fixture
def mock_builder() -> BaseCarBuilder:
    """
    Returns an initialized BaseCarBuilder object.
    """

    return BaseCarBuilder()


@pytest.fixture
def mock_ctx():
    """
    Factory for creating SessionStateContext instances.
    """

    defaults = {
        "drivers": [
            {"UserName": "Driver1", "CarNumber": "12"},
            {"UserName": "Driver2", "CarNumber": "8"},
        ],
        "positions": [1, 2],
        "class_positions": [0, 1],
        "lap_dist_pct": [0.3, 0.6],
        "is_pitroad": [False, True],
        "multiclass": False,
    }

    def _make_ctx(**overrides):
        data = {**defaults, **overrides}
        return SessionStateContext(**data)

    return _make_ctx
