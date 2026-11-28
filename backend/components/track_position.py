from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class CarPositionContext:
    """
    Position of one car on the track with the data to turn it into time.

    Built once per snapshot by a feature service from the iRacing telemetry
    arrays (one entry per car index) and the car's driver info, and passed
    to the track components (TimeGapComponent, TrackTimeLineComponent)
    instead of loose numbers, so a calculation always gets the data of one
    car together.

    Values are taken from iRacing as they are and may be invalid
    (a negative lap distance, a missing time); the components check them.

    Example:

        A GT3 Ferrari halfway around Le Mans:

        CarPositionContext(
            lap_dist_pct=0.5,       # CarIdxLapDistPct
            est_time=115.36,        # CarIdxEstTime
            est_lap_time=230.72,    # DriverInfo.Drivers[i].CarClassEstLapTime
            class_id=4074,          # DriverInfo.Drivers[i].CarClassID
        )

    Attributes:
        lap_dist_pct (float | None):
            Part of the lap the car has covered since the S/F line, from 0.0
            to 1.0 (CarIdxLapDistPct). Negative when the car is not on the
            track (in the garage, towed, disconnected).
        est_time (float | None):
            Time the car's model needs from the S/F line to this point at its
            reference pace (CarIdxEstTime). It depends only on the car model
            and the point, not on how the car is actually driven.
        est_lap_time (float | None):
            Reference lap time of the car's model (CarClassEstLapTime): the
            time scale of `est_time`. Car models of one class can differ by
            a second or two (GT3, GT4).
        class_id (int | None):
            Car class of the car (CarClassID).
    """

    lap_dist_pct: Any = None
    est_time: Any = None
    est_lap_time: Any = None
    class_id: int | None = None


class TrackPositionComponent:
    """
    Positions of cars along the lap: validity of a lap distance and the
    distance between two cars across the S/F line.
    """

    @staticmethod
    def is_on_track(lap_dist_pct: Any) -> bool:
        """
        Return True when a lap distance can be used for position math.

        iRacing sends a negative CarIdxLapDistPct (usually -1) for a car
        that is not on the track: in the garage, being towed or disconnected.

        Example:

            is_on_track(0.0)   -> True     # on the S/F line
            is_on_track(0.73)  -> True
            is_on_track(-1)    -> False    # not on the track
            is_on_track(None)  -> False    # no telemetry for the car

        Args:
            lap_dist_pct: Lap distance of a car (CarIdxLapDistPct).

        Returns:
            True for a number from 0.0 up, otherwise False.
        """
        return isinstance(lap_dist_pct, (int, float)) and lap_dist_pct >= 0

    @classmethod
    def distance_gap(cls, reference_dist: Any, target_dist: Any) -> float | None:
        """
        Return the shortest signed distance from the reference car to the
        target car, in laps.

        iRacing lap distance goes from 0.0 to 1.0 and starts from 0.0 again
        at the S/F line, so whole laps are removed from the difference (see
        wrap_to_nearest_lap). Cars close to each other across the line stay
        close; a car more than half a lap up the road is closer from behind.
        Whole laps between the cars (lapped cars) do not change the distance
        gap; see LapRelationComponent for them.

        Example:

            reference = 0.45, target = 0.47
                0.47 - 0.45 = 0.02                -> 0.02 (2% of a lap ahead)

            reference = 0.98, target = 0.02
                0.02 - 0.98 = -0.96 -> +1 lap     -> 0.04 (ahead, past the line)

            reference = 0.1, target = 0.7
                0.7 - 0.1 = 0.6 -> -1 lap         -> -0.4 (40% of a lap behind)

            reference = 0.5, target = -1          -> None (target off track)

            On a 4 km track 0.02 lap is 80 m.

        Args:
            reference_dist: Lap distance of the reference car (CarIdxLapDistPct).
            target_dist: Lap distance of the target car (CarIdxLapDistPct).

        Returns:
            Laps from -0.5 to 0.5: positive when the target is ahead,
            negative when it is behind, 0.0 when level. None when either
            car is not on the track.
        """
        if not (cls.is_on_track(reference_dist) and cls.is_on_track(target_dist)):
            return None

        return cls.wrap_to_nearest_lap(target_dist - reference_dist, 1.0)

    @staticmethod
    def wrap_to_nearest_lap(value: float, lap: float) -> float:
        """
        Remove whole laps from a difference of two positions on the lap.

        Lap distance and estimated time start from 0 again at the S/F line,
        so the plain difference of two cars close to each other across the
        line is almost a whole lap. The nearest whole number of laps is
        removed, which leaves the shortest way between the two points:
        within half a lap in both directions.

        Works for any unit of the lap: laps (lap = 1.0) or seconds
        (lap = reference lap time).

        Example:

            Lap distance (lap = 1.0):

                reference = 0.98, target = 0.02
                difference = 0.02 - 0.98 = -0.96
                -0.96 - round(-0.96) * 1.0 = -0.96 + 1.0 = 0.04

                The target is 4% of a lap ahead, just past the line.

            Time (lap = 100.0 s):

                reference = 98.0 s, target = 2.0 s
                difference = 2.0 - 98.0 = -96.0
                -96.0 - round(-0.96) * 100.0 = -96.0 + 100.0 = 4.0

                The target is 4 s ahead.

        Args:
            value: Difference of two positions, target minus reference.
            lap: Length of one lap in the units of `value`; must be positive.

        Returns:
            The difference between -lap / 2 and lap / 2: positive when the
            target is ahead, negative when it is behind.
        """
        return value - round(value / lap) * lap
