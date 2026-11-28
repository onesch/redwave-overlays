import math
from typing import Any

from backend.components.lap_time import LapTimeComponent
from backend.components.track_position import (
    CarPositionContext,
    TrackPositionComponent,
)

# The lap is split into this many equal segments: about 2-14 m of track
# per segment on real tracks (2.4 km Lime Rock - 13.6 km Le Mans).
SEGMENTS_PER_LAP = 1000

# Interpolate only between filled segments at most this far apart. At 10
# samples per second a fast car on a short track skips 2-3 segments between
# samples; a wider hole, or data on one side only, is not trusted.
MAX_INTERPOLATION_SPAN = 5


class TrackTimeLineComponent:
    """
    Time line of the lap for one car: lap distance -> seconds from the S/F
    line at that car's reference pace, learned from the cars of its class.

    The time line answers "how long does this car need to get from point A
    to point B of the track", which is the time gap to a car at point B as
    the in-game timing shows it. It is learned, not calculated:

    1. CarIdxEstTime is the time a car model needs from the S/F line to its
       current point at the model's reference pace. It depends only on the
       model and the point, so every car on the track shows one point of
       its model's time line at every sample.

    2. A class can mix car models (GT3, GT4) whose reference laps
       (CarClassEstLapTime) differ by a second or two, and CarIdxEstTime of
       each model runs on its own time scale. The models of one class share
       the speed profile over the lap, only the scale differs, so a sample
       is rescaled to the time line's car:
       est_time * time line lap / model lap.

    3. Samples are averaged per lap segment (SEGMENTS_PER_LAP). Cars of
       another class are not recorded: their speed profile over the lap is
       different and would distort the time line. They are not needed
       either: the cars of the time line's class cover the whole track.

    4. A point between segment centers is interpolated from the nearest
       filled segments on both sides (MAX_INTERPOLATION_SPAN). Where the
       time line has no data yet (the first lap) it returns None and the
       caller uses a fallback.

    The time line only grows with the lap distance, so the time gaps it
    gives are always ordered like the cars on the track, for cars of any
    class.

    It belongs to one track, class and car and is kept across snapshots by
    the service that owns it; `bind()` clears it when any of them changes.
    Sessions of the same track (practice, qualifying, race) share the time
    line.

    Example:

        Ferrari 296 GT3 at Le Mans, reference lap 230.72 s. One snapshot
        records three cars of the class:

            Ferrari at 0.5003, est_time 115.40, model lap 230.72
                -> segment 500, 115.40 * 230.72 / 230.72 = 115.40
            BMW at 0.5007, est_time 116.43, model lap 232.76
                -> segment 500, 116.43 * 230.72 / 232.76 = 115.41
            Porsche at 0.5014, est_time 115.81, model lap 231.15
                -> segment 501, 115.81 * 230.72 / 231.15 = 115.59

        Segment 500 (0.500-0.501) is 115.405 s, the average of two samples,
        and segment 501 (0.501-0.502) is 115.59 s.
    """

    def __init__(self, segments: int = SEGMENTS_PER_LAP):
        self._segments = segments
        self._track_id: Any = None
        self._class_id: Any = None
        self._est_lap_time: float | None = None
        self.clear()

    def clear(self) -> None:
        """
        Forget all samples; the binding to the track, class and car is kept.

        Each segment keeps the sum of its rescaled samples and their count,
        so its value is the average and memory does not grow over a session.
        """
        self._time_sums = [0.0] * self._segments
        self._sample_counts = [0] * self._segments

    def bind(self, track_id: Any, class_id: Any, est_lap_time: Any) -> None:
        """
        Bind the time line to a track, a car class and the car it describes;
        clear the time line when any of them changes.

        Called before recording every snapshot. The car is identified by its
        reference lap time: it is the time scale the time line is kept in, and it
        changes when the player switches to another car model of the class.

        Example:

            bind(252, 4074, 230.72)   # first call: binds, the time line is empty
            bind(252, 4074, 230.72)   # same binding: the time line is kept
            bind(252, 4074, 232.76)   # another GT3 model: the time line is cleared
            bind(341, 4074, 230.72)   # another track: the time line is cleared
            bind(252, 4074, None)     # no reference lap: cleared and unbound,
                                      # record() and time_at() are ignored

        Args:
            track_id: Track of the session (WeekendInfo.TrackID).
            class_id: Car class of the time line's car (CarClassID).
            est_lap_time: Reference lap of the time line's car (CarClassEstLapTime).

        Returns:
            None.
        """
        if not LapTimeComponent.is_valid_lap_time(est_lap_time):
            est_lap_time = None

        binding = (track_id, class_id, est_lap_time)

        if binding != (self._track_id, self._class_id, self._est_lap_time):
            self._track_id, self._class_id, self._est_lap_time = binding
            self.clear()

    def record(self, car: CarPositionContext) -> None:
        """
        Record one sample of a car of the time line's class.

        The car's CarIdxEstTime is rescaled from its model's reference lap
        to the time line's lap and added to the segment of its lap distance.
        Choosing which cars to record (the time line's class, not in the pits,
        not the pace car) is up to the caller.

        Example:

            Time line lap 230.72 s (Ferrari), a BMW of the class records:

                lap_dist_pct = 0.5007, est_time = 116.43, est_lap_time = 232.76

                segment = int(0.5007 * 1000) = 500
                sample  = 116.43 * 230.72 / 232.76 = 115.41

                segment 500 gets +115.41 s and one more sample.

        Args:
            car: Lap distance, CarIdxEstTime and the reference lap of the
                car's model.

        Returns:
            None. A sample without a valid lap distance or time is ignored,
            as is every sample while the time line has no reference lap.
        """
        if self._est_lap_time is None:
            return

        if not LapTimeComponent.is_valid_lap_time(car.est_lap_time):
            return

        if (
            not TrackPositionComponent.is_on_track(car.lap_dist_pct)
            or car.lap_dist_pct >= 1
        ):
            return

        if not LapTimeComponent.is_valid_lap_time(car.est_time):
            return

        segment = int(car.lap_dist_pct * self._segments)
        self._time_sums[segment] += (
            car.est_time * self._est_lap_time / car.est_lap_time
        )
        self._sample_counts[segment] += 1

    def time_at(self, lap_dist_pct: Any) -> float | None:
        """
        Return the time from the S/F line to a point of the track at the
        time line's car pace.

        A segment's value belongs to its center. The point is interpolated
        linearly between the nearest filled segments on both sides, at most
        MAX_INTERPOLATION_SPAN segments apart.

        Example:

            Segment 500 (center 0.5005) = 50.0 s
            Segment 501                 = empty
            Segment 502 (center 0.5025) = 51.0 s

            time_at(0.5015) -> 50.5     # halfway between the two centers
            time_at(0.5005) -> 50.0     # on the center of segment 500

            Segments 498 and 499 filled, nothing after them:
            time_at(0.5015) -> None     # data on one side only

        Args:
            lap_dist_pct: Point of the track (CarIdxLapDistPct).

        Returns:
            Seconds from the S/F line, or None for an invalid point or when
            the time line has no data close around it.
        """
        if (
            not TrackPositionComponent.is_on_track(lap_dist_pct)
            or lap_dist_pct >= 1
        ):
            return None

        # Position in segments, measured from the center of segment 0.
        # The epsilon keeps a point right on a center in that segment
        # despite float rounding.
        position = lap_dist_pct * self._segments - 0.5
        base = math.floor(position + 1e-9)
        lower = self._nearest_filled(base, step=-1)
        upper = self._nearest_filled(base + 1, step=1)

        if lower is None or upper is None:
            return None

        if upper - lower > MAX_INTERPOLATION_SPAN:
            return None

        lower_time = self._segment_time(lower)
        upper_time = self._segment_time(upper)

        return lower_time + (upper_time - lower_time) * (
            (position - lower) / (upper - lower)
        )

    def time_between(self, reference_dist: Any, target_dist: Any) -> float | None:
        """
        Return the time the time line's car needs from the reference point to the
        target point: the time gap to a car at the target point.

        The difference of the two times is wrapped across the S/F line
        by the time line's lap (see TrackPositionComponent.wrap_to_nearest_lap).

        Example:

            Time line lap 100.0 s:

            reference = 0.20 -> time_at = 20.0
            target    = 0.25 -> time_at = 26.0  (a slow chicane)
            26.0 - 20.0 = 6.0                    -> 6.0 s ahead

            reference = 0.98 -> time_at = 98.0
            target    = 0.02 -> time_at =  2.0
            2.0 - 98.0 = -96.0, wrapped          -> 4.0 s ahead

            reference = 0.25, target = 0.20      -> -6.0 s (behind)

        Args:
            reference_dist: Lap distance of the reference car, usually
                the player (CarIdxLapDistPct).
            target_dist: Lap distance of the target car (CarIdxLapDistPct).

        Returns:
            Seconds, positive when the target is ahead, negative when it is
            behind, within half a lap. None when the time line is not bound to
            a reference lap or has no data at either point.
        """
        if self._est_lap_time is None:
            return None

        reference_time = self.time_at(reference_dist)
        target_time = self.time_at(target_dist)

        if reference_time is None or target_time is None:
            return None

        return TrackPositionComponent.wrap_to_nearest_lap(
            target_time - reference_time,
            self._est_lap_time,
        )

    def _nearest_filled(self, start: int, step: int) -> int | None:
        """
        Return the nearest filled segment from `start` in the `step`
        direction (-1 back, +1 forward), within MAX_INTERPOLATION_SPAN.
        """
        for i in range(MAX_INTERPOLATION_SPAN + 1):
            segment = start + i * step

            if not 0 <= segment < self._segments:
                return None

            if self._sample_counts[segment]:
                return segment

        return None

    def _segment_time(self, segment: int) -> float:
        """Return the average rescaled time of a filled segment."""
        return self._time_sums[segment] / self._sample_counts[segment]
