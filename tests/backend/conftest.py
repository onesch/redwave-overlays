import pytest
from unittest.mock import MagicMock

from backend.services.irsdk.service import IRSDKService


@pytest.fixture
def irsdk_mock_factory():
    """
    IRSDK mock factory with custom values.
    """

    def _factory(values: dict = None, is_connected=True):
        base_values = {"Speed": 10.0}
        if values:
            base_values.update(values)

        mock_ir = MagicMock()
        mock_ir.is_initialized = True
        mock_ir.is_connected = is_connected
        mock_ir.__getitem__.side_effect = lambda key: base_values.get(key)
        mock_ir.get_value = lambda key: base_values.get(key)
        mock_ir._ensure_connected = lambda: (is_connected, "")

        mock_ir.startup = MagicMock()

        return mock_ir

    return _factory


@pytest.fixture
def mock_irsdk_service(irsdk_mock_factory):
    """
    Returns the IRSDKService initialized with mock irsdk.
    """
    irsdk = IRSDKService()
    irsdk.ir = irsdk_mock_factory()
    irsdk.started = True
    return irsdk
