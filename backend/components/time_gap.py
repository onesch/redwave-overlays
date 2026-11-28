from backend.components.car_class import CarClassComponent
from backend.components.lap_time import LapTimeComponent
from backend.components.track_position import (
    CarPositionContext,
    TrackPositionComponent,
)
from backend.components.track_time_line import TrackTimeLineComponent


class TimeGapComponent:
    """
    Calculates the time gap from a reference car (usually the player) to
    a target car, in seconds.

    The gap is signed (positive when the target is ahead), takes the shortest
    way between the cars across the S/F line (within half a lap) and is
    measured at the reference car's pace: how long the reference car needs
    to get where the target car is now, as the in-game timing shows it.

    Sources, from the most accurate:

    1. The reference car's time line (TrackTimeLineComponent), for a target
       of any class. Always ordered like the cars on the track.
    2. Until the time line has data at both points (the first lap):
       - a target of the same class: CarIdxEstTime of both cars, the
         target's rescaled to the reference car's model (GT3 models differ
         by a second or two per lap, the speed profile is the same);
       - a target of another class: the distance gap times the reference
         lap. Another class has its own speed profile over the lap, so its
         CarIdxEstTime is wrong by several tenths even level with the
         reference car; the distance is exact close by.
    """

    def time_gap(
        self,
        reference: CarPositionContext,
        target: CarPositionContext,
        time_line: TrackTimeLineComponent | None = None,
    ) -> float | None:
        """
        Return the time gap from the reference car to the target car at the
        reference car's pace, in seconds.

        The source is chosen from the most accurate available (see the class
        docstring): the time line, then the rescaled CarIdxEstTime for the
        same class, then the distance gap for another class.

        Example:

            Reference: GT3 at 0.20, reference lap 100.0 s. The track has
            a slow chicane between 0.20 and 0.25.

            Target: LMP2 at 0.25.
                The time line is filled:
                    time_line.time_between(0.20, 0.25) = 26.0 - 20.0 -> 6.0
                The time line has no data there yet (another class):
                    distance_gap = 0.05, 0.05 * 100.0                -> 5.0

            Target: GT3 of another model (reference lap 102.0) at 0.25,
            CarIdxEstTime 27.54, reference CarIdxEstTime 20.0.
                The time line has no data there yet (same class):
                    27.54 * 100.0 / 102.0 - 20.0 = 27.0 - 20.0       -> 7.0

        Args:
            reference: Position of the reference car, usually the player.
            target: Position of the target car.
            time_line: Time line of the reference car, if the caller keeps
                one.

        Returns:
            Seconds, positive when the target is ahead, negative when it is
            behind, within half a lap. None when the chosen source has no
            data (no CarIdxEstTime, no reference lap, a car off track).
        """
        if time_line is not None:
            time_line_gap = time_line.time_between(
                reference.lap_dist_pct,
                target.lap_dist_pct,
            )

            if time_line_gap is not None:
                return time_line_gap

        if CarClassComponent.is_same_class(reference.class_id, target.class_id):
            return self._est_time_gap(reference, target)

        return self._distance_time_gap(reference, target)

    @staticmethod
    def _est_time_gap(
        reference: CarPositionContext,
        target: CarPositionContext,
    ) -> float | None:
        """
        Return the time gap from CarIdxEstTime of two cars of the same class.

        The target's CarIdxEstTime is on its model's time scale; when both
        reference laps are known it is rescaled to the reference car's model.
        The difference is wrapped across the S/F line by the reference lap;
        without a reference lap it is neither rescaled nor wrapped.

        Example:

            GT3 at Le Mans, the cars level with each other at 0.5:

            reference: est_time 115.0,  est_lap_time 230.0 (Ferrari)
            target:    est_time 116.15, est_lap_time 232.3 (BMW)

            116.15 * 230.0 / 232.3 = 115.0
            115.0 - 115.0                  -> 0.0
            (without rescaling: 116.15 - 115.0 = 1.15 s ahead, wrong)

        Args:
            reference: Position of the reference car.
            target: Position of a target car of the same class.

        Returns:
            Seconds, positive when the target is ahead. None when either
            car has no CarIdxEstTime.
        """
        if not (
            LapTimeComponent.is_valid_lap_time(reference.est_time)
            and LapTimeComponent.is_valid_lap_time(target.est_time)
        ):
            return None

        reference_lap = reference.est_lap_time
        target_est_time = target.est_time

        if LapTimeComponent.is_valid_lap_time(
            reference_lap
        ) and LapTimeComponent.is_valid_lap_time(target.est_lap_time):
            target_est_time = target.est_time * reference_lap / target.est_lap_time

        gap = target_est_time - reference.est_time

        if LapTimeComponent.is_valid_lap_time(reference_lap):
            gap = TrackPositionComponent.wrap_to_nearest_lap(gap, reference_lap)

        return gap

    @staticmethod
    def _distance_time_gap(
        reference: CarPositionContext,
        target: CarPositionContext,
    ) -> float | None:
        """
        Return the time gap from the distance gap at the reference car's
        average lap pace.

        Exact close by, less accurate far away: the reference car is faster
        on straights and slower in corners than its average pace.

        Example:

            reference = 0.500, target = 0.503, reference lap 115.25 s
            distance_gap = 0.003, 0.003 * 115.25  -> 0.35 s ahead

        Args:
            reference: Position of the reference car.
            target: Position of the target car.

        Returns:
            Seconds, positive when the target is ahead. None when either car
            is not on the track or the reference lap is unknown.
        """
        distance = TrackPositionComponent.distance_gap(
            reference.lap_dist_pct,
            target.lap_dist_pct,
        )

        if distance is None:
            return None

        if not LapTimeComponent.is_valid_lap_time(reference.est_lap_time):
            return None

        return distance * reference.est_lap_time
