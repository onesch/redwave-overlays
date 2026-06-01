import time
from typing import Any, Literal

from backend.services.base import BaseCarBuilder, BaseService
from backend.services.leaderboard.car_sorter import CarSorter
from backend.services.leaderboard.context import LeaderboardContext
from backend.services.leaderboard.lap_times.formatter import TimeFormatter
from backend.services.leaderboard.lap_times.service import LapTimeService
from backend.services.leaderboard.neighbords import NeighborsService


class CarDataBuilder(BaseCarBuilder):
    """Responsible for constructing leaderboard car data entries."""

    def __init__(self, irsdk_service, lap_times: LapTimeService):
        self.irsdk = irsdk_service
        self.lap_times = lap_times or LapTimeService()
        self._last_pit_laps: dict[int, int] = {}
        self._pit_exit_times: dict[int, float] = {}

    def reset_pit_data(self):
        """Reset pit tracking when session changes."""
        self._last_pit_laps.clear()
        self._pit_exit_times.clear()

    def build(
        self, idx: int, ctx: LeaderboardContext
    ) -> dict[str, Any] | None:
        """Generates driver data for the leaderboard."""
        base_car = super().build(idx, ctx)
        if not base_car:
            return None

        driver: dict[str, Any] = ctx.drivers[idx]
        class_id = driver.get("CarClassID")
        last_lap_seconds = ctx.last_lap_times[idx]

        return {
            **base_car,
            "pos": self._resolve_position(idx, ctx),
            "name": self._get_first_name(driver),
            "irating": driver.get("IRating"),
            "license": driver.get("LicString"),
            "car_class_color": driver.get("CarClassColor"),
            "lap_dist_pct": self._format_lap_dist(idx, ctx),
            "last_pit_lap": self._get_last_pit_lap(idx, ctx.laps_started, ctx.is_pitroad),
            "laps_started": ctx.laps_started[idx],
            "last_lap_time_formatted": TimeFormatter.format_lap_time(last_lap_seconds),
            "last_lap_seconds": last_lap_seconds,
            "best_lap_seconds": ctx.best_lap_times[idx],
            "session_fastest_lap_seconds": self.lap_times.session_fastest_lap(ctx),
            "class_fastest_lap_seconds": self.lap_times.class_fastest_lap(ctx, class_id),
        }

    def build_all(
        self, ctx: LeaderboardContext, exclude_idx: int | None = None
    ) -> list[dict[str, Any]]:
        """Return all cars for snapshot, optionally excluding a player."""
        cars: list[dict[str, Any]] = [
            car
            for idx in range(len(ctx.drivers))
            if idx != exclude_idx and (car := self.build(idx, ctx))
        ]
        return CarSorter.sort(cars)

    def _is_pace_car(self, driver: dict) -> bool:
        """Checks if a car is a pace car by name."""
        return driver.get("UserName", "").upper() == "PACE CAR"

    def _get_first_name(self, driver: dict) -> str:
        names = driver.get("UserName", "").strip().split()
        return names[0] if names else ""

    def _format_lap_dist(self, idx: int, ctx: LeaderboardContext) -> float:
        dist: float = ctx.lap_dist_pct[idx]
        return round(dist, 3) if isinstance(dist, float) and dist >= 0 else None

    def _resolve_position(self, idx: int, ctx: LeaderboardContext) -> int | None:
        """
        Return the car's effective position,
        using class positions if multiclass.
        Returns None if unknown, or calculates starting position if zero.
        """
        pos_list = ctx.class_positions if ctx.multiclass else ctx.positions
        pos = pos_list[idx]

        if pos == -1:
            return None
        if pos == 0:
            return self._get_starting_position(
                idx,
                "ClassPosition" if ctx.multiclass else "Position",
                1 if ctx.multiclass else 0,
            )
        return pos

    def _get_starting_position(
        self, car_idx: int, field: str, offset: int
    ) -> int:
        """
        Get the car's starting position from
        session results, adding an offset.
        Returns 0 if not found.
        """
        session_info: dict[str, Any] = self.irsdk.get_value("SessionInfo") or {}
        sessions: list[dict[str, Any]] = session_info.get("Sessions", [])

        for sess in sessions:
            if sess.get("SessionType") in (
                "Warmup",
                "Lone Qualify",
                "Open Qualify",
            ):
                for res in sess.get("ResultsPositions") or []:
                    if res.get("CarIdx") == car_idx:
                        return int(res.get(field, 0)) + offset
        return 0

    def _get_last_pit_lap(
        self, idx: int, laps_started: list[int], is_pitroad: list[bool]
    ) -> str | None:
        """Returns the last lap the car was in pitroad."""
        now = time.time()

        if is_pitroad[idx]:
            self._last_pit_laps[idx] = laps_started[idx]
            self._pit_exit_times.pop(idx, None)
            return f"IN L{laps_started[idx]}"

        if idx in self._last_pit_laps:
            if idx not in self._pit_exit_times:
                self._pit_exit_times[idx] = now
                return f"OUT L{self._last_pit_laps[idx]}"
            if now - self._pit_exit_times[idx] <= 5:
                return f"OUT L{self._last_pit_laps[idx]}"
            return f"L{self._last_pit_laps[idx]}"

        return None


class Leaderboard(BaseService):
    """Main service for building leaderboard telemetry data."""

    def __init__(self, irsdk_service):
        self.lap_times = LapTimeService()
        builder = CarDataBuilder(irsdk_service, self.lap_times)
        super().__init__(irsdk_service, builder)
        self.neighbors = NeighborsService(builder)
        self._last_session_num: int | None = None

    def _build_snapshot(self, ctx: LeaderboardContext) -> dict[str, Any]:
        """Build the leaderboard snapshot using prepared context."""
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

        return LeaderboardContext(
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

    def get_session_time(
        self,
        current_session: dict,
        player_lap_time: float | None,
        is_format: bool = True,
    ) -> str | float:
        """
        Public method to get the session time.

        Calculates the session duration using lap-based timing if available,
        otherwise falls back to total session time.
        Returns a formatted string if requested.
        """
        session_time_total: float = self.irsdk.get_value("SessionTimeTotal")
        lap_calculated_time = self.lap_times.calculate_session_time_based_on_laps(
            current_session,
            player_lap_time,
        )

        if lap_calculated_time is not None:
            session_time = lap_calculated_time
            is_lap_calculated_time = True
        else:
            session_time = session_time_total
            is_lap_calculated_time = False

        if is_format:
            formatted = TimeFormatter.format_session_time(
                session_time,
                show_seconds=False,
            )
            return f"~{formatted}" if is_lap_calculated_time else formatted

        return session_time

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

        session_time = self.get_session_time(
            current_session,
            player_lap_time,
            is_format=False,
        )
        resolved_session_time_current = TimeFormatter.format_session_time(
            session_time_current,
            show_seconds=True,
        )
        session_time_formatted = self.get_session_time(
            current_session,
            player_lap_time,
            is_format=True,
        )

        return {
            "session_laps": session_laps,
            "player_lap_time": player_lap_time,
            "session_time": session_time,
            "session_time_current": resolved_session_time_current,
            "session_time_formatted": session_time_formatted,
        }

    def _is_multiclass(self, drivers: list) -> bool:
        """Check if race contains multiple car classes."""
        return len(
            {d.get("CarClassID") for d in drivers if d.get("CarClassID")}
        ) > 1

    def _normalize_laps_started(self, raw_laps: list[Any]) -> list[int]:  # ! need tests
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
