from dataclasses import dataclass, field

from backend.components.track_position import CarPositionContext
from backend.components.track_time_line import TrackTimeLineComponent
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
        car_positions (dict[int, CarPositionContext]):
            Track position of each car with its lap distance, estimated
            time, reference lap and class, keyed by car index. Cars missing
            from the telemetry arrays are not included.
        lap_deltas (dict[int, int]):
            Whole laps each car is ahead (positive) or behind (negative) of
            the player, keyed by car index (see LapRelationComponent).
        track_time_line (TrackTimeLineComponent):
            Time line of the lap at the player's car pace, learned from the
            player's class; used for the time gaps to all cars.
        pit_labels (dict[int, str]):
            Pit label of each car with a pit stop ("IN L5", "OUT L6", "L6"),
            keyed by car index (see PitStopComponent).

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
    car_positions: dict[int, CarPositionContext] = field(default_factory=dict)
    # Set in Leaderboard._build_context().
    lap_deltas: dict[int, int] = field(default_factory=dict)
    # Time line of the player's car, kept by Leaderboard across snapshots.
    track_time_line: TrackTimeLineComponent = field(
        default_factory=TrackTimeLineComponent
    )
    # Set in Leaderboard._build_context().
    pit_labels: dict[int, str] = field(default_factory=dict)
