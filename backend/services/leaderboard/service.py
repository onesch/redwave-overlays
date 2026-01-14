import time
from dataclasses import dataclass
from typing import Any, Dict, List, Literal


@dataclass
class LeaderboardContext:
    """
    Container for leaderboard telemetry data for a racing session.

    Attributes:
        drivers (list[dict]):
            List of dictionaries with info for each driver.
        positions (list[int]):
            Overall track positions of the cars.
        class_positions (list[int]):
            Positions within each car class
            (for multiclass races).
        last_lap_times (list[float]):
            Last lap time of each driver in seconds.
        laps_started (list[int]):
            Number of laps started by each driver.
        lap_dist_pct (list[float]):
            Fraction of current lap completed
            by each driver (0.0–1.0).
        is_pitroad (list[bool]):
            Flags indicating if a car is currently
            on the pit road.
        multiclass (bool):
            True if the race has multiple car classes.

    Used by NeighborsService, CarDataBuilder and Leaderboard to construct
    and sort leaderboard telemetry data.
    """

    drivers: list[dict]
    positions: list[int]
    class_positions: list[int]
    last_lap_times: list[float]
    laps_started: list[int]
    lap_dist_pct: list[float]
    is_pitroad: list[bool]
    multiclass: bool


class TimeFormatter:
    """Utility for formatting lap and session times."""

    @staticmethod
    def format_lap_time(seconds: float) -> str:
        """Convert lap time in seconds to '--:--.---' format."""
        if seconds is None or seconds <= 0:
            return "--:--.---"
        ms = int(seconds * 1000)
        s = ms // 1000
        ms_remain = ms % 1000
        m = s // 60
        s = s % 60
        return f"{m:02d}:{s:02d}.{ms_remain:03d}"

    @staticmethod
    def format_session_time(seconds: float, is_seconds: bool) -> str:
        """
        Format session time from seconds
        to 'HH:MM:SS' or 'MM:SS' format.
        """
        if seconds is None or seconds < 0:
            return "--:--.---"

        hrs = int(seconds // 3600)
        mins = int((seconds % 3600) // 60)
        secs_remain = int(seconds % 60)

        if is_seconds:
            return (
                f"{hrs:02d}:{mins:02d}:{secs_remain:02d}h"
                if hrs > 0
                else f"{mins:02d}:{secs_remain:02d}m"
            )
        return (
            f"{hrs:02d}:{mins:02d}h" if hrs > 0 else f"{hrs:02d}:{mins:02d}m"
        )


class CarDataBuilder:
    """Responsible for constructing car data entries."""

    def __init__(self, irsdk_service):
        self.irsdk = irsdk_service
        self._last_pit_laps: dict[int, int] = {}
        self._pit_exit_times: dict[int, float] = {}

    def reset_pit_data(self):
        """Reset pit tracking when session changes."""
        self._last_pit_laps.clear()
        self._pit_exit_times.clear()

    def build(
        self, idx: int | None, ctx: LeaderboardContext
    ) -> dict[str, Any] | None:
        """Generates driver data for the leaderboard."""
        driver: dict[str, Any] = ctx.drivers[idx]
        car_number: str = driver.get("CarNumber")
        irating: int = driver.get("IRating")
        license_str: str = driver.get("LicString")
        car_class_color: int = driver.get("CarClassColor")
        last_lap: str = TimeFormatter.format_lap_time(ctx.last_lap_times[idx])
        is_in_pitroad: bool = ctx.is_pitroad[idx]

        if self._is_pace_car(driver):
            return None

        laps_started: int = ctx.laps_started[idx]
        if laps_started < 0:
            laps_started = 0

        return {
            "pos": self._resolve_position(idx, ctx),
            "car_idx": idx,
            "car_number": car_number,
            "name": self._get_first_name(driver),
            "laps_started": laps_started,
            "last_lap": last_lap,
            "irating": irating,
            "license": license_str,
            "car_class_color": car_class_color,
            "lap_dist_pct": self._format_lap_dist(idx, ctx),
            "is_in_pitroad": is_in_pitroad,
            "last_pit_lap": self._get_last_pit_lap(
                idx, ctx.laps_started, ctx.is_pitroad
            ),
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
        return (
            round(dist, 3) if isinstance(dist, float) and dist >= 0 else None
        )

    def _resolve_position(
        self, idx: int, ctx: LeaderboardContext
    ) -> int | None:
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
        session_info: dict[str, Any] = (
            self.irsdk.get_value("SessionInfo") or {}
        )
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
        self, idx: int, laps_started: List[int], is_pitroad: List[bool]
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


class CarSorter:
    """Utility class for sorting car data dictionaries."""

    @staticmethod
    def sort(cars: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Sort cars by position, keeping None or 0 at the end."""
        return sorted(
            cars,
            key=lambda c: (
                c["pos"] is None or c["pos"] == 0,
                c["pos"] if isinstance(c["pos"], int) else 9999,
            ),
        )


class NeighborsService:
    """
    Service responsible for finding and formatting neighboring cars
    (ahead and behind the player) based on lap distance.
    """

    def __init__(self, builder):
        self.builder = builder

    def get_neighbors(self, player_idx, ctx) -> dict:
        """
        Return neighboring cars ahead and behind the player.
        """
        ahead, behind = self._collect_candidates(player_idx, ctx)
        ahead, behind = self._sort_candidates(ahead, behind)
        return self._format_neighbors(ahead, behind)

    def _calc_gap(
        self, my_dist: float, dist: float, est_lap_time: float
    ) -> dict[str, float | None] | None:
        """
        Calculate the lap and time gap between the player and another car.
        """
        if not isinstance(dist, (int, float)) or dist < 0:
            return None

        gap_pct = (dist - my_dist) % 1.0
        gap_sec = gap_pct * est_lap_time if est_lap_time else None
        return {"gap_pct": gap_pct, "gap_sec": gap_sec}

    def _collect_candidates(
        self, player_idx: int, ctx: LeaderboardContext
    ) -> tuple[list[dict], list[dict]]:
        """Collect all potential neighboring cars around the player."""
        my_dist: float = ctx.lap_dist_pct[player_idx]
        my_est_lap_time: float = (
            ctx.drivers[player_idx]
            .get("CarClassEstLapTime")
        )

        ahead, behind = [], []

        for idx, dist in enumerate(ctx.lap_dist_pct):
            if idx == player_idx:
                continue
            if idx >= len(ctx.drivers):
                continue
            car_data = self.builder.build(idx, ctx)
            if not car_data:
                continue

            gap = self._calc_gap(my_dist, dist, my_est_lap_time)
            if not gap:
                continue

            lap_diff = ctx.laps_started[idx] - ctx.laps_started[player_idx]
            car_data["lap_status"] = (
                "ahead_lap"
                if lap_diff > 0
                else "behind_lap" if lap_diff < 0 else None
            )

            if 0 < gap["gap_pct"] <= 0.5:
                ahead.append({"car": car_data, **gap})
            elif gap["gap_pct"] > 0.5:
                behind.append(
                    {
                        "car": car_data,
                        "gap_pct": gap["gap_pct"] - 1.0,
                        "gap_sec": (gap["gap_pct"] - 1.0) * my_est_lap_time,
                    }
                )

        return ahead, behind

    @staticmethod
    def _sort_candidates(
        ahead: list[dict], behind: list[dict]
    ) -> tuple[list[dict], list[dict]]:
        """Sort neighboring cars in-place by their distance to the player."""
        ahead.sort(key=lambda x: x["gap_pct"])
        behind.sort(key=lambda x: x["gap_pct"], reverse=True)
        return ahead, behind

    @staticmethod
    def _format_neighbors(
        ahead: list[dict], behind: list[dict], limit=3
    ) -> dict[str, list[dict]]:
        """
        Format neighboring car data for external use.

        Limits the number of cars returned and normalizes gap values,
        returning a structure ready for API or UI consumption.
        """

        def fmt(c):
            return {
                **c["car"],
                "gap_pct": round(abs(c["gap_pct"]), 3),
                "gap_sec": (
                    round(abs(c["gap_sec"]), 2) if c["gap_sec"] else None
                ),
            }

        return {
            "ahead": [fmt(c) for c in ahead[:limit]],
            "behind": [fmt(c) for c in behind[:limit]],
        }


class Leaderboard:
    """Main service for building leaderboard telemetry data."""

    def __init__(self, irsdk_service):
        self.irsdk = irsdk_service
        self.builder = CarDataBuilder(irsdk_service)
        self.neighbors = NeighborsService(self.builder)
        self._last_session_num: int = None

    def _is_multiclass(self, drivers: list) -> bool:
        """Check if race contains multiple car classes."""
        return (
            len({d.get("CarClassID") for d in drivers if d.get("CarClassID")})
            > 1
        )

    def get_leaderboard_snapshot(self) -> Dict[str, Any]:
        """Return a snapshot of leaderboard data with player context."""
        self.irsdk._ensure_connected()

        ctx = self._build_context()
        if ctx is None:
            return self._empty_snapshot()

        player_idx: int = self.irsdk.get_value("PlayerCarIdx")

        return {
            "cars": self.builder.build_all(ctx, exclude_idx=player_idx),
            "player": self.builder.build(player_idx, ctx),
            "neighbors": self.neighbors.get_neighbors(player_idx, ctx),
            "leaderboard_data": self.get_session_info(player_idx, ctx),
            "multiclass": ctx.multiclass,
        }

    def _build_context(self) -> LeaderboardContext | None:
        driver_info: dict[str, Any] = (
            self.irsdk.get_value("DriverInfo") or {}
        )
        drivers: list[dict[str, Any]] = driver_info.get("Drivers", []) or {}

        if not drivers:
            return None

        raw_laps: list[int] = self.irsdk.get_value("CarIdxLap") or []
        laps_started = [
            lap if isinstance(lap, int) and lap >= 0 else 0
            for lap in raw_laps
        ]

        multiclass = self._is_multiclass(drivers)

        return LeaderboardContext(
            drivers=drivers,
            positions=self.irsdk.get_value("CarIdxPosition") or [],
            class_positions=self.irsdk.get_value("CarIdxClassPosition") or [],
            last_lap_times=self.irsdk.get_value("CarIdxLastLapTime") or [],
            laps_started=laps_started,
            lap_dist_pct=self.irsdk.get_value("CarIdxLapDistPct") or [],
            is_pitroad=self.irsdk.get_value("CarIdxOnPitRoad") or [],
            multiclass=multiclass,
        )

    def _empty_snapshot(self) -> dict[str, Any]:
        return {
            "status": "waiting",
            "player": None,
            "cars": [],
            "neighbors": {"ahead": [], "behind": []},
            "leaderboard_data": None,
            "multiclass": False,
        }

    def _get_estimated_lap_time(
        self,
        player_idx: int,
        ctx: LeaderboardContext,
    ) -> float | None:
        """Return estimated lap time."""
        driver = ctx.drivers[player_idx]

        est_lap = driver.get("CarClassEstLapTime")

        if not isinstance(est_lap, (int, float)):
            return None

        if est_lap <= 0:
            return None

        return est_lap

    def _get_best_lap_time(
        self,
        player_idx: int,
        ctx: LeaderboardContext,
    ) -> float | None:
        """Return best lap time."""
        best_laps = self.irsdk.get_value("CarIdxBestLapTime")

        best_lap = best_laps[player_idx]

        if not isinstance(best_lap, (int, float)):
            return None

        if best_lap <= 0:
            return None

        return best_lap

    def get_car_lap_time(
        self,
        player_idx: int,
        ctx: LeaderboardContext,
    ) -> float:
        """Returns best or estimated lap time."""

        best_lap = self._get_best_lap_time(player_idx, ctx)
        if best_lap is not None:
            return best_lap

        est_lap = self._get_estimated_lap_time(player_idx, ctx)
        if est_lap is not None:
            return est_lap

    def get_session_time(
        self,
        current_session: dict,
        player_lap_time: float,
        is_format: bool = True,
    ) -> str | float:
        """
        Public method to get the session time.

        Calculates the session duration using lap-based timing if available,
        otherwise falls back to total session time.
        Returns a formatted string if requested.
        """
        session_time_total: float = self.irsdk.get_value("SessionTimeTotal")
        lap_calculated_time = self._calculate_session_time_based_on_laps(
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
                is_seconds=False,
            )
            return f"~{formatted}" if is_lap_calculated_time else formatted

        return session_time

    def _calculate_session_time_based_on_laps(
        self,
        current_session: dict,
        player_lap_time: float,
    ) -> float | None:
        """Calculates session time based on the number of laps."""
        session_laps: int | Literal["unlimited"] = current_session.get(
            "SessionLaps"
        )
        session_type: str = current_session.get("SessionType", "")

        if session_laps != "unlimited" and session_type == "Race":
            return session_laps * player_lap_time
        return None

    def get_session_info(
        self,
        player_idx: int,
        ctx: LeaderboardContext,
    ) -> Dict[str, Any]:
        """Public method returning structured session info for a player."""
        session_info: dict[str, Any] = (
            self.irsdk.get_value("SessionInfo") or {}
        )
        current_session = self._get_current_session(session_info)

        self._reset_pit_status(session_info)

        session_laps: int | Literal["unlimited"] = current_session.get(
            "SessionLaps"
        )
        session_time_current: float = self.irsdk.get_value("SessionTime")

        player_lap_time = self.get_car_lap_time(player_idx, ctx)

        session_time = self.get_session_time(
            current_session,
            player_lap_time,
            is_format=False,
        )
        resolved_session_time_current = TimeFormatter.format_session_time(
            session_time_current,
            is_seconds=True,
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
