from typing import Any, Literal

from backend.services.base import BaseService
from backend.services.leaderboard.car_data_builder import CarDataBuilder
from backend.services.leaderboard.context import LeaderboardContext
from backend.services.leaderboard.lap_times.formatter import TimeFormatter
from backend.services.leaderboard.lap_times.service import LapTimeService
from backend.services.leaderboard.neighbords import NeighborsService


class Leaderboard(BaseService):
    """Main service for building leaderboard telemetry data."""

    def __init__(self, irsdk_service):
        self.lap_times = LapTimeService()
        builder = CarDataBuilder(irsdk_service, self.lap_times)
        super().__init__(irsdk_service, builder)
        self.neighbors = NeighborsService(builder)
        self._last_session_num: int | None = None

    def _build_snapshot(self, ctx: LeaderboardContext) -> dict[str, Any]:
        player_idx: int = self.irsdk.get_value("PlayerCarIdx")

        return {
            "status": "ok",
            "cars": self.builder.build_all(ctx, exclude_idx=player_idx),
            "player": self.builder.build(player_idx, ctx),
            "neighbors": self.neighbors.get_neighbors(player_idx, ctx),
            "leaderboard_data": self.get_session_info(player_idx, ctx),
            "multiclass": ctx.multiclass,
        }

    def _build_context(self) -> LeaderboardContext | None:
        driver_info: dict[str, Any] = self.irsdk.get_value("DriverInfo") or {}
        drivers: list[dict[str, Any]] = driver_info.get("Drivers", []) or []

        if not drivers:
            return None

        ctx = LeaderboardContext(
            drivers=drivers,
            positions=self.irsdk.get_value("CarIdxPosition") or [],
            class_positions=self.irsdk.get_value("CarIdxClassPosition") or [],
            last_lap_times=self.irsdk.get_value("CarIdxLastLapTime") or [],
            best_lap_times=self.irsdk.get_value("CarIdxBestLapTime") or [],
            laps_started=self._normalize_laps_started(
                self.irsdk.get_value("CarIdxLap") or []
            ),
            lap_dist_pct=self.irsdk.get_value("CarIdxLapDistPct") or [],
            is_pitroad=self.irsdk.get_value("CarIdxOnPitRoad") or [],
            multiclass=self._is_multiclass(drivers),
        )

        ctx.session_fastest_lap = self.lap_times.session_fastest_lap(ctx)
        ctx.class_fastest_laps = {
            class_id: self.lap_times.class_fastest_lap(ctx, class_id)
            for class_id in {driver.get("CarClassID") for driver in drivers}
        }

        return ctx

    def get_session_time(
        self,
        current_session: dict,
        player_lap_time: float | None,
    ) -> tuple[float, bool]:
        """
        Calculate session time and whether it was derived from lap count.
        Returns (session_time, is_approximate).
        """
        lap_calculated = self.lap_times.calculate_session_time_based_on_laps(
            current_session,
            player_lap_time,
        )
        if lap_calculated is not None:
            return lap_calculated, True
        return self.irsdk.get_value("SessionTimeTotal"), False

    def get_session_info(
        self,
        player_idx: int,
        ctx: LeaderboardContext,
    ) -> dict[str, Any]:
        """Public method returning structured session info for a player."""
        session_info: dict[str, Any] = self.irsdk.get_value("SessionInfo") or {}
        current_session = self._get_current_session(session_info)

        self._reset_pit_status(session_info)

        session_laps: int | Literal["unlimited"] = current_session.get("SessionLaps")
        session_time_current: float = self.irsdk.get_value("SessionTime")

        player_lap_time = self.lap_times.car_lap_time(player_idx, ctx)

        session_time, is_approximate = self.get_session_time(
            current_session, player_lap_time,
        )
        resolved_session_time_current = TimeFormatter.format_session_time(
            session_time_current, show_seconds=True,
        )
        session_time_formatted = TimeFormatter.format_session_time(
            session_time, show_seconds=False,
        )

        return {
            "session_laps": session_laps,
            "player_lap_time": player_lap_time,
            "session_time": session_time,
            "session_time_current": resolved_session_time_current,
            "session_time_formatted": f"~{session_time_formatted}" if is_approximate else session_time_formatted,
        }

    def _is_multiclass(self, drivers: list) -> bool:
        """Check if race contains multiple car classes."""
        return len(
            {d.get("CarClassID") for d in drivers if d.get("CarClassID")}
        ) > 1

    def _normalize_laps_started(self, raw_laps: list[Any]) -> list[int]:
        """
        Replace invalid lap counts with 0.
        Negative values, non-integers, and None are treated as 0.
        """
        return [
            lap if isinstance(lap, int) and lap >= 0 else 0
            for lap in raw_laps
        ]

    def _reset_pit_status(self, session_info: dict) -> None:
        """Reset pit tracking if a new session has started."""
        current_num = session_info.get("CurrentSessionNum", 0)

        if self._last_session_num != current_num:
            self.builder.reset_pit_data()
            self._last_session_num = current_num

    def _get_current_session(self, session_info: dict) -> dict:
        """Return the current session dictionary from session info."""
        sessions = session_info.get("Sessions", [])
        current_num = session_info.get("CurrentSessionNum", 0)
        return sessions[current_num] if current_num < len(sessions) else {}
