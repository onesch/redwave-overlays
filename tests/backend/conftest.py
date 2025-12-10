import pytest
from unittest.mock import MagicMock

from backend.services.irsdk.service import IRSDKService
from backend.services.irsdk.parser import IRSDKParser
from backend.services.radar.service import RadarService


@pytest.fixture
def irsdk_mock_factory():
    def _factory(values: dict, connected=True):
        mock_ir = MagicMock()
        mock_ir.is_initialized = True
        mock_ir.is_connected = connected

        mock_ir.__getitem__.side_effect = lambda key: values.get(key)
        mock_ir.get_value = lambda key: values.get(key)

        return mock_ir

    return _factory


@pytest.fixture
def mock_service(irsdk_mock_factory):
    def _factory(values=None, connected=True):
        base_values = {
            "Speed": 10.0,
            "Throttle": 0.7,
            "BrakeRaw": 0.2,
            "WeekendInfo": {"TrackLength": "3000 m"},
        }
        if values:
            base_values.update(values)

        mock_ir = irsdk_mock_factory(base_values, connected=connected)

        irsdk_service = IRSDKService()
        irsdk_service.ir = mock_ir
        irsdk_service.started = True

        parser = IRSDKParser(irsdk_service)
        return RadarService(irsdk_service, parser)
    return _factory


@pytest.fixture
def parser(mock_service):
    return IRSDKParser(mock_service)

@pytest.fixture
def mock_irsdk_leaderboard(irsdk_mock_factory):
    values = {
        "CarIdxPosition": [1, 2, 3],
        "CarIdxClassPosition": [0, 1, 2],
        "CarIdxLap": [5, 5, 4],
        "CarIdxLastLapTime": [80.0, 81.5, 82.2],
        "CarIdxLapDistPct": [0.6, 0.3, 0.9],
        "CarIdxOnPitRoad": [False, False, False],
        "PlayerCarIdx": 0,
        "SessionTime": 100.0,
        "SessionTimeTotal": 100.0,
        "DriverInfo": {
            "Drivers": [
                {
                    "UserName": "Driver1",
                    "IRating": 2000,
                    "LicString": "A 4.99",
                    "CarNumber": "12",
                    "CarClassColor": 16711680,
                    "CarClassID": 1,
                    "CarClassEstLapTime": 80.0,
                },
                {
                    "UserName": "Driver2",
                    "IRating": 1800,
                    "LicString": "B 3.12",
                    "CarNumber": "8",
                    "CarClassColor": 16711680,
                    "CarClassID": 1,
                    "CarClassEstLapTime": 80.0,
                },
                {
                    "UserName": "Driver3",
                    "IRating": 1700,
                    "LicString": "C 2.50",
                    "CarNumber": "99",
                    "CarClassColor": 16711680,
                    "CarClassID": 1,
                    "CarClassEstLapTime": 80.0,
                },
            ]
        },
        "SessionInfo": {
            "CurrentSessionNum": 1,
            "Sessions": [
                {
                    "SessionType": "Lone Qualify",
                    "SessionLaps": "2",
                    "SessionTime": "20 sec",
                    "ResultsFastestLap": [
                        {"CarIdx": 0, "FastestTime": 88.8},
                        {"CarIdx": 1, "FastestTime": 89.1},
                    ],
                    "ResultsPositions": [
                        {"CarIdx": 0, "Position": 1},
                        {"CarIdx": 1, "Position": 2},
                    ],
                },
                {
                    "SessionType": "Race",
                    "SessionLaps": "10",
                    "SessionTime": "100 sec",
                    "ResultsFastestLap": [
                        {"CarIdx": 0, "FastestTime": 79.8},
                        {"CarIdx": 1, "FastestTime": 81.0},
                        {"CarIdx": 2, "FastestTime": 99.1},
                    ],
                    "ResultsPositions": [
                        {"CarIdx": 0, "Position": 1},
                        {"CarIdx": 2, "Position": 3},
                    ],
                },
            ],
        },
    }
    return irsdk_mock_factory(values)



@pytest.fixture
def mock_irsdk_leaderboard_multiclass(irsdk_mock_factory):
    drivers = [
        {"UserName": "Driver1", "CarClassID": 1},
        {"UserName": "Driver2", "CarClassID": 2},
    ]
    values = {
        "DriverInfo": {"Drivers": drivers},
        "CarIdxOnPitRoad": [False, False],
        "PlayerCarIdx": 0,
        "CarIdxPosition": [1, 2],
        "CarIdxClassPosition": [0, 0],
        "CarIdxLastLapTime": [74.0, 77.0],
        "CarIdxLap": [5, 5],
        "CarIdxLapDistPct": [0.2, 0.1],
        "SessionInfo": {"Sessions": []},
    }
    return irsdk_mock_factory(values)
