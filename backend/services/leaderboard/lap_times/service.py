from typing import Any, Iterable, Literal

from backend.services.leaderboard.context import LeaderboardContext


class LapTimeService:
    """Encapsulates Leaderboard service lap-time selection and calculations."""

    @staticmethod
    def is_valid_lap_time(lap_time: Any) -> bool:
        """Return True when a telemetry value can be used as a lap time."""
        return isinstance(lap_time, (int, float)) and lap_time > 0

    def fastest_lap(self, lap_times: Iterable[Any]) -> float | None:
        """Return the fastest valid lap from an arbitrary collection."""
        valid_laps = [
            lap_time
            for lap_time in lap_times
            if self.is_valid_lap_time(lap_time)
        ]
        return min(valid_laps) if valid_laps else None

    def session_fastest_lap(self, ctx: LeaderboardContext) -> float | None:
        """Return the fastest valid best lap across the session."""
        return self.fastest_lap(ctx.best_lap_times)

    def class_fastest_lap(
        self,
        ctx: LeaderboardContext,
        class_id: int | None,
    ) -> float | None:
        """Return the fastest valid best lap for a specific car class."""
        class_laps = (
            ctx.best_lap_times[idx]
            for idx, driver in enumerate(ctx.drivers)
            if idx < len(ctx.best_lap_times) and driver.get("CarClassID") == class_id
        )
        return self.fastest_lap(class_laps)

    def best_lap_time(
        self,
        player_idx: int,
        ctx: LeaderboardContext,
    ) -> float | None:
        """Return a driver's valid best lap time from context."""
        if player_idx >= len(ctx.best_lap_times):
            return None

        best_lap = ctx.best_lap_times[player_idx]
        return best_lap if self.is_valid_lap_time(best_lap) else None

    def estimated_lap_time(
        self,
        player_idx: int,
        ctx: LeaderboardContext,
    ) -> float | None:
        """Return a driver's valid car-class estimated lap time."""
        if player_idx >= len(ctx.drivers):
            return None

        estimated_lap = ctx.drivers[player_idx].get("CarClassEstLapTime")
        return estimated_lap if self.is_valid_lap_time(estimated_lap) else None

    def car_lap_time(
        self,
        player_idx: int,
        ctx: LeaderboardContext,
    ) -> float | None:
        """Return the best available player lap time for session estimates."""
        return self.best_lap_time(player_idx, ctx) or self.estimated_lap_time(
            player_idx,
            ctx,
        )

    def calculate_session_time_based_on_laps(
        self,
        current_session: dict[str, Any],
        player_lap_time: float | None,
    ) -> float | None:
        """Calculate race duration from lap count and player lap time."""
        session_laps: int | Literal["unlimited"] = current_session.get("SessionLaps")
        session_type: str = current_session.get("SessionType", "")

        if (
            session_laps != "unlimited"
            and session_type == "Race"
            and player_lap_time is not None
        ):
            return session_laps * player_lap_time
        return None
