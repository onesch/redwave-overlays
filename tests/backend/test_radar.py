import pytest

from backend.services.radar.constants import (
    CLR_LEFT,
    CLR_RIGHT,
    CLR_BOTH,
    CLR_TWO_LEFT,
    CLR_TWO_RIGHT,
)


# --- Data tests ---


def test_track_length_zero(mock_irsdk_radar):
    radar = mock_irsdk_radar({"WeekendInfo": {"TrackLength": "0 m"}})
    snapshot = radar.get_snapshot()

    if not snapshot["status"] == "ok":
        assert snapshot == {"status": "waiting", "cars": []}


def test_distances_within_range(mock_irsdk_radar):
    radar = mock_irsdk_radar(
        {
            "CarDistAhead": 4.0,
            "CarDistBehind": 6.0,
            "CarLeftRight": 0,
        }
    )
    snapshot = radar.get_snapshot()
    assert snapshot["ahead_m"] == 4.0
    assert snapshot["ahead_severity"] == "red"
    assert snapshot["behind_m"] == 6.0
    assert snapshot["behind_severity"] == "yellow"
    assert snapshot["left"] is None
    assert snapshot["right"] is None


@pytest.mark.parametrize(
    "clr,expected_left,expected_right",
    [
        (CLR_LEFT, {"severity": "red"}, None),
        (CLR_RIGHT, None, {"severity": "red"}),
        (CLR_BOTH, {"severity": "red"}, {"severity": "red"}),
        (CLR_TWO_LEFT, {"severity": "red"}, None),
        (CLR_TWO_RIGHT, None, {"severity": "red"}),
    ],
)
def test_car_on_side(
    mock_irsdk_radar, clr, expected_left, expected_right
):
    radar = mock_irsdk_radar(
        {
            "CarDistAhead": 5.0,
            "CarDistBehind": 6.0,
            "CarLeftRight": clr,
        }
    )
    snapshot = radar.get_snapshot()
    assert snapshot["ahead_m"] is None
    assert snapshot["behind_m"] is None
    assert snapshot["left"] == expected_left
    assert snapshot["right"] == expected_right


# --- Error tests ---


def test_not_connected(mock_irsdk_radar):
    radar = mock_irsdk_radar(is_connected=False)
    snapshot = radar.get_snapshot()
    assert snapshot == {"status": "waiting", "cars": []}


def test_distances_out_of_range(mock_irsdk_radar):
    radar = mock_irsdk_radar(
        {
            "CarDistAhead": 20.0,
            "CarDistBehind": -1.0,
            "CarLeftRight": 0,
        }
    )
    snapshot = radar.get_snapshot()
    assert snapshot["ahead_m"] is None
    assert snapshot["ahead_severity"] == "none"
    assert snapshot["behind_m"] is None
    assert snapshot["behind_severity"] == "none"
