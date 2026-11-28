# Seconds a car keeps the "OUT" label after leaving the pit road.
PIT_EXIT_HOLD_SEC = 5


class PitStopComponent:
    """
    Pit stops of every car, followed across snapshots.

    Telemetry only tells whether a car is on the pit road right now
    (CarIdxOnPitRoad). The lap of the last pit stop and the moment the car
    left the pit road are remembered here, so the leaderboard can still
    show the stop after the car is back on the track.

    Update it once per snapshot with update(), then read the labels with
    labels(). Clear it when the session changes or restarts.
    """

    def __init__(self) -> None:
        # Lap the car was on when last seen on the pit road, by car index.
        self._pit_laps: dict[int, int] = {}
        # Time the car left the pit road, by car index.
        self._exit_times: dict[int, float] = {}

    def clear(self) -> None:
        """
        Forget all pit stops.

        Called when the session changes or restarts: pit stops of the old
        session are not shown in the new one.

        Returns:
            None.
        """
        self._pit_laps.clear()
        self._exit_times.clear()

    def update(
        self,
        laps_started: list[int],
        is_pitroad: list[bool],
        now: float,
    ) -> None:
        """
        Record the pit road state of every car for this snapshot.

        A car on the pit road stores its current lap and drops its exit
        time. A car that has a pit stop and is back on the track stores the
        first moment it was seen out of the pits; later snapshots keep that
        moment, so the "OUT" label lasts PIT_EXIT_HOLD_SEC from the exit.

        Example:

            now = 1000.0

            car 0: on the pit road, lap 5     -> pit lap 5, no exit time
            car 1: pit lap 6, back on track   -> exit time 1000.0
            car 2: never in the pits          -> nothing stored

        Args:
            laps_started: Laps started by car index (normalized CarIdxLap).
            is_pitroad: Pit road state by car index (CarIdxOnPitRoad).
            now: Current time in seconds (time.time()).

        Returns:
            None. Cars missing from either array are not updated.
        """
        count = min(len(laps_started), len(is_pitroad))

        for idx in range(count):
            if is_pitroad[idx]:
                self._pit_laps[idx] = laps_started[idx]
                self._exit_times.pop(idx, None)
            elif idx in self._pit_laps:
                self._exit_times.setdefault(idx, now)

    def labels(self, now: float) -> dict[int, str]:
        """
        Return the pit label of every car with a pit stop, ready to show.

        A stop on lap 0 (before the start) has no lap to show, so the label
        says "PIT" instead, and nothing once the "OUT" label is over.

        Example:

            PIT_EXIT_HOLD_SEC = 5, now = 1000.0

            car 0: on the pit road, lap 5                -> "IN L5"
            car 1: pit lap 6, left at 997.0  (3 s ago)   -> "OUT L6"
            car 2: pit lap 6, left at 990.0  (10 s ago)  -> "L6"
            car 3: on the pit road, lap 0                -> "IN PIT"
            car 4: pit lap 0, left at 997.0              -> "OUT PIT"
            car 5: pit lap 0, left at 990.0              -> no label
            car 6: never in the pits                     -> no label

        Args:
            now: Current time in seconds, the same as passed to update().

        Returns:
            Pit labels keyed by car index.
        """
        labels: dict[int, str] = {}

        for idx, lap in self._pit_laps.items():
            label = self._label(lap, self._exit_times.get(idx), now)
            if label:
                labels[idx] = label

        return labels

    @staticmethod
    def _label(lap: int, exit_time: float | None, now: float) -> str | None:
        """
        Return the pit label of one car.

        Args:
            lap: Lap of the pit stop.
            exit_time: Time the car left the pit road, None while in it.
            now: Current time in seconds.

        Returns:
            "`IN ...`", "`OUT ...`", "`L<lap>`" or `None`.
        """
        lap_text = f"L{lap}" if lap > 0 else "PIT"

        if exit_time is None:
            return f"IN {lap_text}"

        if now - exit_time <= PIT_EXIT_HOLD_SEC:
            return f"OUT {lap_text}"

        return f"L{lap}" if lap > 0 else None
