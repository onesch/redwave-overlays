import time
from typing import Any

from backend.services.leaderboard.car_sorter import CarSorter
from backend.services.base import BaseCarBuilder
from backend.services.leaderboard.context import LeaderboardContext
from backend.services.leaderboard.lap_times.formatter import TimeFormatter
from backend.services.leaderboard.lap_times.service import LapTimeService


class CarDataBuilder(BaseCarBuilder):
    """Responsible for constructing leaderboard car data entries."""

    def __init__(self, irsdk_service, lap_times: LapTimeService):
        self.irsdk = irsdk_service
        self.lap_times = lap_times
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
        class_id: int = driver.get("CarClassID")
        last_lap_seconds: float = ctx.last_lap_times[idx]

        return {
            **base_car,
            "driver_id": driver.get("UserID", idx),
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
            "session_fastest_lap_seconds": ctx.session_fastest_lap,
            "class_fastest_lap_seconds": ctx.class_fastest_laps.get(class_id),
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

    def _get_first_name(self, driver: dict) -> str:
        names = driver.get("UserName", "").strip().split()
        return names[0] if names else ""

    def get_irating_drivers(
        self,
        ctx: LeaderboardContext,
    ) -> list[dict[str, Any]]:
        """
        Build driver data required for iRating calculation.
        """
        drivers = []

        for car_idx, driver in enumerate(ctx.drivers):
            if self._is_pace_car(driver):
                continue

            position = self._resolve_position(car_idx, ctx)
            started = position is not None and position > 0

            irating = driver.get("IRating")
            if not isinstance(irating, int) or irating <= 0:
                continue

            drivers.append(
                {
                    "id": driver.get("UserID", car_idx),
                    "irating": irating,
                    "position": position,
                    "class_id": driver.get("CarClassID"),
                    "started": started,
                }
            )

        return sorted(
            drivers,
            key=lambda d: (
                d["position"] is None,
                d["position"] or 9999,
            ),
        )

    def _format_lap_dist(self, idx: int, ctx: LeaderboardContext) -> float:
        dist: float = ctx.lap_dist_pct[idx]
        return round(dist, 3) if isinstance(dist, float) and dist >= 0 else None

    def _resolve_position(
        self,
        idx: int,
        ctx: LeaderboardContext,
    ) -> int | None:
        """
        Return the car's effective position.

        Uses current telemetry position when available.
        Falls back to the starting position from QualifyResultsInfo
        when the current position is zero.
        """
        positions: list[int] = (
            ctx.class_positions
            if ctx.multiclass
            else ctx.positions
        )

        position = positions[idx]

        if position == -1:
            return None

        if position > 0:
            return position

        starting_positions: dict[int, int] = (
            ctx.starting_class_positions
            if ctx.multiclass
            else ctx.starting_positions
        )

        return starting_positions.get(idx)

    def get_starting_positions(
        self,
    ) -> tuple[dict[int, int], dict[int, int]]:
        """
        Return starting overall and class positions from
        QualifyResultsInfo.

        Returns:
            Tuple containing:
                - overall starting positions by car index
                - class starting positions by car index
        """
        qualify_info: dict[str, Any] = (
            self.irsdk.get_value("QualifyResultsInfo") or {}
        )

        qualify_results: list[dict[str, Any]] = (
            qualify_info.get("Results") or []
        )

        starting_positions = {}
        starting_class_positions = {}

        for result in qualify_results:
            car_idx = result.get("CarIdx")

            if car_idx is None:
                continue

            position = result.get("Position")
            class_position = result.get("ClassPosition")

            if position is not None:
                starting_positions[car_idx] = position + 1

            if class_position is not None:
                starting_class_positions[car_idx] = class_position + 1

        return starting_positions, starting_class_positions

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
