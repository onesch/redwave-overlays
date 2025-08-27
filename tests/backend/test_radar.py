import pytest
from unittest.mock import MagicMock

from backend.services.irsdk.parser import IRSDKParser
from backend.services.irsdk.service import IRSDKService
from backend.services.radar.service import RadarService
from backend.services.radar.constants import CLR_LEFT, CLR_RIGHT, CLR_BOTH


@pytest.fixture
def default_radar_values():
    return {
        "WeekendInfo": {"TrackLength": "3000 m"},
        "CarDistAhead": 0.0,
        "CarDistBehind": 0.0,
        "CarLeftRight": 0,
    }


@pytest.fixture
def mock_service(default_radar_values):
    def _factory(values=None, connected=True):
        service = IRSDKService()
        mock_ir = MagicMock()
        mock_ir.is_initialized = True
        mock_ir.is_connected = connected

        final_values = dict(default_radar_values)
        if values:
            final_values.update(values)

        mock_ir.__getitem__.side_effect = lambda key: final_values.get(key)
        service.ir = mock_ir
        service.started = True

        parser = IRSDKParser(service)

        return RadarService(service, parser)

    return _factory


# --- Data tests ---


def test_track_length_zero(mock_service):
    radar = mock_service({"WeekendInfo": {"TrackLength": "0 m"}})
    result = radar.get_radar_json()
    assert result["reason"] == "track_len=0"


def test_distances_within_range(mock_service):
    radar = mock_service(
        {
            "CarDistAhead": 4.0,
            "CarDistBehind": 6.0,
        }
    )
    result = radar.get_radar_json()
    assert result["ahead_m"] == 4.0
    assert result["ahead_severity"] == "red"
    assert result["behind_m"] == 6.0
    assert result["behind_severity"] == "yellow"


@pytest.mark.parametrize(
    "clr,expected_left,expected_right",
    [
        (CLR_LEFT, {"severity": "red"}, None),
        (CLR_RIGHT, None, {"severity": "red"}),
        (CLR_BOTH, {"severity": "red"}, {"severity": "red"}),
    ],
)
def test_car_on_side(mock_service, clr, expected_left, expected_right):
    radar = mock_service(
        {
            "CarDistAhead": 5.0,
            "CarDistBehind": 6.0,
            "CarLeftRight": clr,
        }
    )
    result = radar.get_radar_json()
    assert result["ahead_m"] is None
    assert result["behind_m"] is None
    assert result["left"] == expected_left
    assert result["right"] == expected_right


# --- Error tests ---


def test_not_connected(mock_service):
    radar = mock_service(connected=False)
    result = radar.get_radar_json()
    assert result["reason"] == "not connected"


def test_distances_out_of_range(mock_service):
    radar = mock_service(
        {
            "CarDistAhead": 20.0,
            "CarDistBehind": -1.0,
            "CarLeftRight": 0,
        }
    )
    result = radar.get_radar_json()
    assert result["ahead_m"] is None
    assert result["ahead_severity"] == "none"
    assert result["behind_m"] is None
    assert result["behind_severity"] == "none"
