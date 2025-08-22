import pytest
from unittest.mock import MagicMock
from backend.services.irsdk.service import IRSDKService
from backend.services.irsdk.parser import IRSDKParser


@pytest.fixture
def mock_service(monkeypatch):
    """Mock IRSDKService.ir object to avoid real SDK connection."""
    service = IRSDKService()
    mock_ir = MagicMock()
    mock_ir.is_initialized = True
    mock_ir.is_connected = True
    mock_ir.__getitem__.side_effect = lambda key: {
        "Speed": 10.0,
        "Throttle": 0.7,
        "BrakeRaw": 0.2,
        "WeekendInfo": {"TrackLength": "3.5 km"},
    }.get(key, None)
    service.ir = mock_ir
    service.started = True
    return service


@pytest.fixture
def parser(mock_service):
    return IRSDKParser(mock_service)


# --- Data tests ---


def test_is_connected_true(mock_service):
    assert mock_service.is_connected() is True


def test_get_value_existing(mock_service):
    assert mock_service.get_value("Speed") == 10.0
    assert mock_service.get_value("Throttle") == 0.7
    assert mock_service.get_value("BrakeRaw") == 0.2


def test_get_speed_kmh(parser):
    assert parser.get_speed("kmh") == 36  # 10 m/s -> 36 km/h


def test_get_speed_mph(parser):
    assert parser.get_speed("mph") == 22  # 10 m/s -> 22 mph


def test_get_throttle(parser):
    assert parser.get_throttle() == 70  # 0.7 * 100


def test_get_brake(parser):
    assert parser.get_brake() == 20  # 0.2 * 100


@pytest.mark.parametrize(
    "weekend_info,expected",
    [
        ({"TrackLength": "3.5 km"}, 3500.0),
        ({"TrackLength": "2 mi"}, 3218.688),
        ({"TrackLength": "500 ft"}, 152.4),
        ({"TrackLength": "100 m"}, 100.0),
        ({}, 0.0),
        (None, 0.0),
    ],
)
def test_get_track_length_m(parser, weekend_info, expected):
    assert parser.get_track_length_m(weekend_info) == expected


# --- Error tests ---


def test_get_value_missing(mock_service):
    assert mock_service.get_value("NonExistent") is None


def test_get_speed_invalid(parser):
    assert parser.get_speed("invalid") is None


def test_get_value_when_not_connected(monkeypatch):
    service = IRSDKService()
    service.ir = MagicMock(is_initialized=False, is_connected=False)
    assert service.get_value("Speed") is None


def test_get_track_length_invalid(parser):
    assert parser.get_track_length_m({"TrackLength": "abc"}) == 0.0
