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
    assert mock_irsdk_service.get_value("Speed") == pytest.approx(10.0)


@pytest.mark.parametrize(
    "driver,expected",
    [
        ({"UserName": "PACE CAR"}, True),
        ({"UserName": "pace car"}, True),
        ({"UserName": "Safety Car", "CarIsPaceCar": 1}, True),
        ({"UserName": "Pace Car", "CarIsPaceCar": 0}, True),
        ({"UserName": "Driver1", "CarIsPaceCar": 0}, False),
        ({"UserName": ""}, False),
        ({}, False),
    ],
)
def test_is_pace_car_by_flag_or_name(driver, expected):
    assert IRSDKService.is_pace_car(driver) is expected


@pytest.mark.parametrize(
    "drivers,expected",
    [
        ([{"CarClassID": 1}, {"CarClassID": 1}], False),
        ([{"CarClassID": 1}, {"CarClassID": 2}], True),
        # The pace car has its own class id, which must not count.
        (
            [
                {"CarClassID": 5},
                {"CarClassID": 5},
                {"UserName": "Pace Car", "CarClassID": 11, "CarIsPaceCar": 1},
            ],
            False,
        ),
        # Entries without a class id are ignored.
        ([{"CarClassID": 1}, {"CarClassID": None}, {}], False),
        ([], False),
    ],
)
def test_is_multiclass(drivers, expected):
    assert IRSDKService.is_multiclass(drivers) is expected


@pytest.mark.parametrize(
    "raw_laps,expected",
    [
        ([-1], [0]),
        ([1], [1]),
        ([0], [0]),
        ([None], [0]),
        (["str"], [0]),
        ([5, -1, 3], [5, 0, 3]),
        ([], []),
    ],
)
def test_normalize_laps(raw_laps, expected):
    assert IRSDKService.normalize_laps(raw_laps) == expected


@pytest.mark.parametrize(
    "rgb,expected",
    [
        (0xFF0000, "#ff0000"),
        (0x0000FF, "#0000ff"),
        (0x00000A, "#00000a"),  # zero-padded to six digits
    ],
)
def test_get_class_color(rgb, expected):
    assert IRSDKService.get_class_color(rgb) == expected


def test_get_speed_ms_valid(mock_irsdk_service):
    # iRacing reports 10 m/s; the backend exposes it without converting.
    result = mock_irsdk_service.get_speed_ms()
    assert result == pytest.approx(10.0)


# --- Error tests ---


def test_get_value_missing(mock_irsdk_service):
    assert mock_irsdk_service.get_value("NonExistent") is None


def test_get_value_when_not_connected(irsdk_mock_factory):
    service = IRSDKService()
    service.ir = irsdk_mock_factory(is_connected=False)
    assert service.get_value("Speed") is None


def test_get_speed_ms_none(irsdk_mock_factory):
    service = IRSDKService()

    mock_ir = irsdk_mock_factory()
    service.ir = mock_ir
    service.started = True

    # override get_value
    service.get_value = lambda key: None

    result = service.get_speed_ms()
    assert result == 0.0


@pytest.mark.parametrize(
    "rgb",
    [
        None,
        "16711680",
        0xFFFFFF,  # white stands for "no class color"
    ],
)
def test_get_class_color_returns_none_without_color(rgb):
    assert IRSDKService.get_class_color(rgb) is None


def test_get_speed_ms_invalid(mock_irsdk_service):
    # A malformed telemetry value must not break the snapshot.
    mock_irsdk_service.get_value = lambda key: "not a number"

    assert mock_irsdk_service.get_speed_ms() == 0.0
