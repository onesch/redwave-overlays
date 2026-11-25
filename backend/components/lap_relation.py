from dataclasses import dataclass, field
from typing import Any, Literal, Sequence

# Lap relation of a car as sent to the frontend; None means the same lap.
LapDiff = Literal["ahead_lap", "behind_lap"]


def wrap_gap(raw_gap: float) -> float:
    """
    Convert a lap-position difference into the shortest signed track gap.

    iRacing lap distance wraps from 1.0 back to 0.0 at the start/finish line.
    Removing the nearest whole lap keeps cars close across the S/F line from
    being classified as almost a full lap apart.
    """
    return raw_gap - round(raw_gap)


@dataclass(frozen=True)
class LapRelations:
    """
    Whole-lap difference of each car relative to the reference car.

    Attributes:
        deltas (dict[int, int]):
            Laps the car is ahead (positive) or behind (negative)
            of the reference car, keyed by car index. Cars without valid
            telemetry and the reference car itself are not included.
    """

    deltas: dict[int, int] = field(default_factory=dict)

    def delta(self, idx: int) -> int | None:
        """Return the lap difference of a car, or None if it is unknown."""
        return self.deltas.get(idx)

    def label(self, idx: int) -> LapDiff | None:
        """
        Return the lap relation of a car in the frontend format.

        None for a car on the same lap or without a known lap difference.
        """
        delta = self.deltas.get(idx)

        if not delta:
            return None

        return "ahead_lap" if delta > 0 else "behind_lap"


class LapRelationComponent:
    """
    Calculates how many laps each car is ahead of or behind
    the reference car (usually the player).
    """

    def compute(
        self,
        laps: Sequence[int],
        lap_dist_pct: Sequence[float],
        reference_idx: int | None,
    ) -> LapRelations:
        """
        Calculate the lap difference of every car relative to the reference car.

        Args:
            laps: Normalized lap counts by car index (CarIdxLap).
            lap_dist_pct: Lap distance by car index; negative when the car
                is not on the track (CarIdxLapDistPct).
            reference_idx: Index of the car the relations are measured from.

        Returns:
            Empty relations when the reference car has no valid position.
        """
        if not self._has_position(reference_idx, laps, lap_dist_pct):
            return LapRelations()

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
                other_laps=laps[idx],
                other_dist=lap_dist_pct[idx],
            )

        return LapRelations(deltas)

    @staticmethod
    def lap_delta(
        reference_laps: int,
        reference_dist: float,
        other_laps: int,
        other_dist: float,
    ) -> int:
        """
        Return the whole laps between two cars.

        The covered distance difference is split into whole laps and the
        shortest physical gap: cars close to each other across the S/F line
        stay on the same lap, a car more than half a lap up the road on the
        next lap counts as a lap ahead.
        """
        covered_diff = (other_laps + other_dist) - (
            reference_laps + reference_dist
        )
        return round(covered_diff - wrap_gap(covered_diff))

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

        lap = laps[idx]
        dist = lap_dist_pct[idx]

        return (
            isinstance(lap, int)
            and isinstance(dist, (int, float))
            and dist >= 0
        )
