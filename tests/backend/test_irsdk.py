import pytest

from backend.services.irsdk.service import IRSDKService

# --- Data tests ---


def test_ensure_connected_starts_when_not_started(irsdk_mock_factory):
    service = IRSDKService()
    mock_ir = irsdk_mock_factory()
    service.ir = mock_ir
    service.started = False

    connected, msg = service._ensure_connected()
    assert connected is True
    assert msg == ""
    assert service.started is True
    mock_ir.startup.assert_called_once()


def test_is_connected_true(mock_irsdk_service):
    assert mock_irsdk_service.is_connected() is True


def test_get_value_existing(mock_irsdk_service):
    assert mock_irsdk_service.get_value("Speed") == 10.0
    assert mock_irsdk_service.get_value("Throttle") == 0.7
    assert mock_irsdk_service.get_value("BrakeRaw") == 0.2


@pytest.mark.parametrize(
    "idx,drivers,player_idx,multiclass,expected",
    [
        # no multiclass
        (
            0,
            [
                {"CarClassColor": 0xFF0000},
                {"CarClassColor": 0x00FF00},
                {"CarClassColor": 0x0000FF},
            ],
            None,
            False,
            "#1b2a3a",
        ),
        # multiclass, player car
        (
            1,
            [
                {"CarClassColor": 0xFF0000},
                {"CarClassColor": 0x00FF00},
                {"CarClassColor": 0x0000FF},
            ],
            1,
            True,
            "#1e6cff",
        ),
        # multiclass, another car
        (
            2,
            [
                {"CarClassColor": 0xFF0000},
                {"CarClassColor": 0x00FF00},
                {"CarClassColor": 0x0000FF},
            ],
            0,
            True,
            "rgb(0,0,255)",
        ),
        # idx out of bounds
        (
            10,
            [
                {"CarClassColor": 0xFF0000},
                {"CarClassColor": 0x00FF00},
                {"CarClassColor": 0x0000FF},
            ],
            None,
            False,
            "#1b2a3a",
        ),
        # CarClassColor None
        (0, [{"CarClassColor": None}], None, True, "#1b2a3a"),
    ],
)
def test_get_car_rgb(idx, drivers, player_idx, multiclass, expected):
    assert (
        IRSDKService.get_car_rgb(
            idx=idx,
            drivers=drivers,
            player_idx=player_idx,
            multiclass=multiclass,
        )
        == expected
    )


# --- Error tests ---


def test_get_value_missing(mock_irsdk_service):
    assert mock_irsdk_service.get_value("NonExistent") is None


def test_get_value_when_not_connected(irsdk_mock_factory):
    service = IRSDKService()
    service.ir = irsdk_mock_factory(is_connected=False)
    assert service.get_value("Speed") is None
