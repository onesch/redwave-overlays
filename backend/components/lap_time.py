from typing import Any, Iterable


class LapTimeComponent:
    """
    Lap time values from iRacing: which of them can be used and the fastest
    of a collection.

    iRacing sends 0 or a negative value when a time is unknown: a car without
    a completed lap (CarIdxLastLapTime, CarIdxBestLapTime), a car model
    without a reference lap (CarClassEstLapTime), a car not on the track
    (CarIdxEstTime).
    """

    @staticmethod
    def is_valid_lap_time(lap_time: Any) -> bool:
        """
        Return True when a telemetry value can be used as a time on the lap.

        Used for lap times (CarIdxLastLapTime, CarIdxBestLapTime,
        CarClassEstLapTime) and for the time from the S/F line to a point
        of the lap (CarIdxEstTime): all of them are unknown at 0 or below.

        Example:

            is_valid_lap_time(230.72) -> True
            is_valid_lap_time(1)      -> True
            is_valid_lap_time(0.0)    -> False    # no time yet
            is_valid_lap_time(-1)     -> False
            is_valid_lap_time(None)   -> False
            is_valid_lap_time("80")   -> False

        Args:
            lap_time: A time in seconds from the telemetry.

        Returns:
            True for a number above 0, otherwise False.
        """
        return isinstance(lap_time, (int, float)) and lap_time > 0

    @classmethod
    def fastest_lap(cls, lap_times: Iterable[Any]) -> float | None:
        """
        Return the fastest valid lap time of a collection.

        Invalid values (see is_valid_lap_time) are skipped.

        Example:

            fastest_lap([0, None, 81.2, "80", 79]) -> 79
            fastest_lap([0, None, -1])             -> None

        Args:
            lap_times: Lap times in seconds, e.g. CarIdxBestLapTime.

        Returns:
            The smallest valid lap time, or None without a valid one.
        """
        valid_laps = [
            lap_time
            for lap_time in lap_times
            if cls.is_valid_lap_time(lap_time)
        ]
        return min(valid_laps) if valid_laps else None
