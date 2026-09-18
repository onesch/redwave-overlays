class TimeFormatter:
    """
    Utility class for time formatting.

    Used as a helper class for the Leaderboard service.
    """

    @staticmethod
    def format_lap_time(seconds: float | None) -> str:
        """
        Convert seconds to 'MM:SS.mmm' format.
        """

        if seconds is None or seconds <= 0:
            return "--:--.---"

        total_ms = int(seconds * 1000)

        minutes = total_ms // 60000
        seconds = (total_ms % 60000) // 1000
        milliseconds = total_ms % 1000

        return (
            f"{minutes:02d}:"
            f"{seconds:02d}."
            f"{milliseconds:03d}"
        )

    @staticmethod
    def format_session_time(seconds: float | None, show_seconds: bool) -> str:
        """
        Format session time from seconds
        to 'HH:MM:SS' or 'MM:SS' format.
        """
        if seconds is None or seconds < 0:
            return "--:--"

        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)

        if show_seconds:
            return (
                f"{hours:02d}:{minutes:02d}:{secs:02d}h"
                if hours > 0
                else f"{minutes:02d}:{secs:02d}m"
            )

        return (
            f"{hours:02d}:{minutes:02d}h"
            if hours > 0
            else f"{hours:02d}:{minutes:02d}m"
        )
