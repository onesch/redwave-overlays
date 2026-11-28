from typing import Any, Sequence

from backend.components.track_position import TrackPositionComponent


class LapRelationComponent:
    """
    Calculates how many whole laps each car is ahead of or behind the
    reference car (usually the player), relative to where the cars are on
    the track.

    The lap relation answers "is this car near me on the track racing on my
    lap, or is it lapping me / being lapped by me". It is not the laps down
    in the standings: a car physically behind the reference car can be
    a lap ahead (the leader catching up to lap it).
    """

    def compute(
        self,
        laps: Sequence[int],
        lap_dist_pct: Sequence[float],
        reference_idx: int | None,
    ) -> dict[int, int]:
        """
        Calculate the lap difference of every car relative to the reference
        car.

        Example:

            Reference car 0 on lap 5 at 0.5.

            laps         = [5,   7,   5,   3,   6]
            lap_dist_pct = [0.5, 0.6, 0.7, 0.4, -1]

            compute(laps, lap_dist_pct, reference_idx=0)
                -> {1: 2, 2: 0, 3: -2}

            Car 4 is not on the track and car 0 is the reference car: both
            are left out.

        Args:
            laps: Normalized lap counts by car index (CarIdxLap).
            lap_dist_pct: Lap distance by car index; negative when the car
                is not on the track (CarIdxLapDistPct).
            reference_idx: Index of the car the relations are measured from.

        Returns:
            Whole laps ahead (positive) or behind (negative) by car index.
            Cars without valid telemetry and the reference car are not
            included; empty when the reference car has no valid position.
        """
        if not self._has_position(reference_idx, laps, lap_dist_pct):
            return {}

        reference_laps = laps[reference_idx]
        reference_dist = lap_dist_pct[reference_idx]

        deltas: dict[int, int] = {}

        for idx in range(min(len(laps), len(lap_dist_pct))):
            if idx == reference_idx:
                continue

            if not self._has_position(idx, laps, lap_dist_pct):
                continue

            deltas[idx] = self.lap_delta(
                reference_laps=reference_laps,
                reference_dist=reference_dist,
                target_laps=laps[idx],
                target_dist=lap_dist_pct[idx],
            )

        return deltas

    @staticmethod
    def lap_delta(
        reference_laps: int,
        reference_dist: float,
        target_laps: int,
        target_dist: float,
    ) -> int:
        """
        Return the whole laps between two cars beyond the distance between
        them on the track.

        The covered distance (lap + lap distance) of both cars is compared
        and rounded to whole laps. What is left after rounding is the
        distance between the cars on the track, within half a lap (see
        TrackPositionComponent.distance_gap):

            covered difference = lap delta + distance gap

        So the lap counter alone or the S/F line does not make a car a lap
        ahead; the car has to be a whole lap further than its position on
        the track next to the reference car.

        Example:

            Reference car on lap 5 at 0.90 (covered 5.90).

            Target on lap 6 at 0.10 (covered 6.10):
                6.10 - 5.90 = +0.20 -> round -> 0
                Same lap: just ahead across the S/F line.

            Target on lap 6 at 0.95 (covered 6.95):
                6.95 - 5.90 = +1.05 -> round -> 1
                A lap ahead, 0.05 lap up the road.

            Target on lap 6 at 0.60 (covered 6.60):
                6.60 - 5.90 = +0.70 -> round -> 1
                A lap ahead, 0.30 lap behind on the track: about to lap
                the reference car.

        Args:
            reference_laps: Lap count of the reference car (CarIdxLap).
            reference_dist: Lap distance of the reference car.
            target_laps: Lap count of the target car (CarIdxLap).
            target_dist: Lap distance of the target car.

        Returns:
            Whole laps, positive when the target is ahead, negative when it
            is behind, 0 on the same lap.
        """
        covered_diff = (
            (target_laps + target_dist) - (reference_laps + reference_dist)
        )
        return round(covered_diff)

    @staticmethod
    def is_lap_ahead(delta: int | None) -> bool:
        """
        Return True when a car is at least a lap ahead of the reference car.

        Example:

            is_lap_ahead(1)    -> True
            is_lap_ahead(2)    -> True
            is_lap_ahead(0)    -> False    # same lap
            is_lap_ahead(-1)   -> False    # a lap behind
            is_lap_ahead(None) -> False    # unknown

        Args:
            delta: Lap difference of the car from compute(), or None when
                the car is not in the result.

        Returns:
            True for a positive lap difference.
        """
        return delta is not None and delta > 0

    @staticmethod
    def is_lap_behind(delta: int | None) -> bool:
        """
        Return True when a car is at least a lap behind the reference car.

        Example:

            is_lap_behind(-1)   -> True
            is_lap_behind(-2)   -> True
            is_lap_behind(0)    -> False    # same lap
            is_lap_behind(1)    -> False    # a lap ahead
            is_lap_behind(None) -> False    # unknown

        Args:
            delta: Lap difference of the car from compute(), or None when
                the car is not in the result.

        Returns:
            True for a negative lap difference.
        """
        return delta is not None and delta < 0

    @staticmethod
    def _has_position(
        idx: Any,
        laps: Sequence[int],
        lap_dist_pct: Sequence[float],
    ) -> bool:
        """Return True when a car has a lap count and a valid lap distance."""
        if not isinstance(idx, int) or not (
            0 <= idx < len(laps) and idx < len(lap_dist_pct)
        ):
            return False

        return isinstance(laps[idx], int) and TrackPositionComponent.is_on_track(
            lap_dist_pct[idx]
        )
