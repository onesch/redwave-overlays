from dataclasses import dataclass

from backend.services.base import SessionStateContext


@dataclass
class LeaderboardContext(SessionStateContext):
    """
    Container for leaderboard telemetry data for a racing session.

    Attributes:
        last_lap_times (list[float]):
            Last lap time of each driver in seconds.
        best_lap_times (list[float]):
            Best lap time of each driver in seconds.
        laps_started (list[int]):
            Number of laps started by each driver.

    Used by NeighborsService, CarDataBuilder and Leaderboard to construct
    and sort leaderboard telemetry data.
    """

    last_lap_times: list[float]
    best_lap_times: list[float]
    laps_started: list[int]
