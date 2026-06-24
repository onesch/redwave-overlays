from dataclasses import dataclass, field

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
        session_fastest_lap (float | None):
            Cached fastest valid best lap across the whole session.
        class_fastest_laps (dict[int | None, float | None]):
            Cached fastest valid best lap by car class ID.
            
    Used by NeighborsService, CarDataBuilder and Leaderboard to construct
    and sort leaderboard telemetry data.
    """

    last_lap_times: list[float]
    best_lap_times: list[float]
    laps_started: list[int]
    # Set in Leaderboard._build_context(). None if no valid laps exist.
    session_fastest_lap: float | None = None
    # Set in Leaderboard._build_context(). Keyed by CarClassID.
    class_fastest_laps: dict[int | None, float | None] = field(default_factory=dict)
