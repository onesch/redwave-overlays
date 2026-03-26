import pytest
from typing import Callable

from backend.services.leaderboard.service import (
    CarDataBuilder,
    Leaderboard,
    LeaderboardContext,
    NeighborsService,
)


@pytest.fixture
def mock_service(mock_values: Callable) -> Leaderboard:
    """
    Returns the Leaderboard initialized with mock values.
    """

    return Leaderboard(mock_values())


@pytest.fixture
def mock_builder(mock_values: Callable) -> CarDataBuilder:
    """
    Returns the CarDataBuilder initialized with mock values.
    """

    return CarDataBuilder(mock_values())


@pytest.fixture
def mock_neighbors(mock_builder: CarDataBuilder) -> NeighborsService:
    """
    Returns the NeighborsService initialized with mock_builder.
    """

    return NeighborsService(mock_builder)


@pytest.fixture
def mock_ctx(mock_values: Callable) -> LeaderboardContext:
    """
    Returns the LeaderboardContext with mocked data from mock_values fixture.
    """

    values = mock_values()

    defaults = {
        "drivers": values.get_value("DriverInfo")["Drivers"],
        "positions": values.get_value("CarIdxPosition"),
        "class_positions": values.get_value(
            "CarIdxClassPosition"
        ),
        "last_lap_times": values.get_value(
            "CarIdxLastLapTime"
        ),
        "laps_started": values.get_value("CarIdxLap"),
        "lap_dist_pct": values.get_value("CarIdxLapDistPct"),
        "is_pitroad": values.get_value("CarIdxOnPitRoad"),
        "multiclass": False,
    }

    def _make_ctx(**overrides):
        data = {**defaults, **overrides}
        return LeaderboardContext(**data)

    return _make_ctx


@pytest.fixture
def mock_values(irsdk_mock_factory):
    """
    Return dictionary containing the data
    required for testing the Leaderboard.
    """

    def _factory(is_multiclass: bool = False) -> dict:
        drivers = [
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

        if is_multiclass:
            drivers[1]["CarClassID"] = 2

        values = {
            "CarIdxPosition": [1, 2, 3],
            "CarIdxClassPosition": [0, 1, 2],
            "CarIdxLap": [5, 5, 4],
            "CarIdxLastLapTime": [80.0, 81.5, 82.2],
            "CarIdxBestLapTime": [11.1, 22.2, None],
            "CarIdxLapDistPct": [0.6, 0.3, 0.9],
            "CarIdxOnPitRoad": [False, False, False],
            "PlayerCarIdx": 0,
            "SessionTime": 100.0,
            "SessionTimeTotal": 100.0,
            "DriverInfo": {
                "Drivers": drivers,
            },
            "SessionInfo": {
                "CurrentSessionNum": 1,
                "Sessions": [
                    {
                        "SessionType": "Lone Qualify",
                        "SessionLaps": 2,
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
                        "SessionLaps": 10,
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

    return _factory
