from dataclasses import dataclass


@dataclass
class RadarContext:
    """
    Immutable container with radar-related telemetry data.

    Attributes:
        dist_ahead (float | None):
            Distance to the car ahead in meters.
            None if not available or suppressed.
        dist_behind (float | None):
            Distance to the car behind in meters.
            None if not available or suppressed.
        car_left_right (int):
            Indicator of cars on the left or right sides.
            Used to determine side alerts
            (e.g., CLR_LEFT, CLR_RIGHT, CLR_BOTH).
        lap_dist_pct (list[float]):
            List of lap distance percentages for all cars in the session.
        player_idx (int | None):
            Index of the player's car in the lap_dist_pct list.
            None if not available.
            
    Used by RadarService to pass pre-fetched, consistent telemetry data
    into snapshot builders.
    """
    dist_ahead: float | None
    dist_behind: float | None
    car_left_right: int
    lap_dist_pct: list[float]
    player_idx: int | None
