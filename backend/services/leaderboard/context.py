from dataclasses import dataclass, field

from backend.components.lap_relation import LapRelations
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
        est_times (list[float]):
           Estimated time in seconds from the S/F line to the cars current position.
        irating_deltas (dict[int, int]):
            Calculated iRating delta for each driver, keyed by driver ID.
        sof (int):
            Strength of Field for the displayed leaderboard class.
        starting_positions (dict[int, int]):
            Starting overall positions by car index from
            QualifyResultsInfo.
        starting_class_positions (dict[int, int]):
            Starting class positions by car index from
            QualifyResultsInfo.
        radio_transmit_car_idx (int):
            Car index of the currently transmitting driver, or -1 when the
            radio is idle.
        player_idx (int | None):
            Car index of the player, read once per snapshot.
        lap_relations (LapRelations):
            Lap difference of each car relative to the player.

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
    est_times: list[float] = field(default_factory=list)
    irating_deltas: dict[int, int] = field(default_factory=dict)
    sof: int = 0
    starting_positions: dict[int, int] = field(default_factory=dict)
    starting_class_positions: dict[int, int] = field(default_factory=dict)
    radio_transmit_car_idx: int = -1
    player_idx: int | None = None
    # Set in Leaderboard._build_context().
    lap_relations: LapRelations = field(default_factory=LapRelations)
