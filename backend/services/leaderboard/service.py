import time
from typing import Any, Literal

from backend.components.car_class import CarClassComponent
from backend.components.lap_relation import LapRelationComponent
from backend.components.pit_stop import PitStopComponent
from backend.components.track_position import CarPositionContext
from backend.components.track_time_line import TrackTimeLineComponent
from backend.services.base import BaseService
from backend.services.irsdk.service import IRSDKService
from backend.services.leaderboard.car_data_builder import CarDataBuilder
from backend.services.leaderboard.context import LeaderboardContext
from backend.services.leaderboard.lap_times.formatter import TimeFormatter
from backend.services.leaderboard.lap_times.service import LapTimeService
from backend.services.leaderboard.neighbors import NeighborsService
from backend.utils.irating_calculation import IRatingCalculator


class Leaderboard(BaseService):
    """Main service for building leaderboard telemetry data."""

    def __init__(self, irsdk_service):
        self.lap_times = LapTimeService()
        builder = CarDataBuilder(irsdk_service, self.lap_times)
        super().__init__(irsdk_service, builder)
        self.neighbors = NeighborsService(builder)
        self.irating_calculator = IRatingCalculator()
        self.lap_relation = LapRelationComponent()
        # Learned across snapshots, so it lives in the service.
        self.track_time_line = TrackTimeLineComponent()
        self.pit_stops = PitStopComponent()
        self._last_session_num: int | None = None
        self._last_session_time: float | None = None

    def _build_snapshot(self, ctx: LeaderboardContext) -> dict[str, Any]:
        # Read once in _build_context(): the snapshot and the context
        # calculations (SOF, lap deltas) must use the same player car.
        player_idx = ctx.player_idx

        return {
            "status": "ok",
            "cars": self.builder.build_all(ctx, exclude_idx=player_idx),
            "player": self.builder.build(player_idx, ctx),
            "neighbors": self.neighbors.get_neighbors(player_idx, ctx),
            "leaderboard_data": {
                **self.get_session_info(player_idx, ctx),
                "sof": ctx.sof,
            },
            "multiclass": ctx.multiclass,
            "irating_deltas": ctx.irating_deltas,
        }

    def _build_context(self) -> LeaderboardContext | None:
        driver_info: dict[str, Any] = self.irsdk.get_value("DriverInfo") or {}
        drivers: list[dict[str, Any]] = driver_info.get("Drivers", []) or []
        player_idx: int = self.irsdk.get_value("PlayerCarIdx")

        if not drivers:
            return None

        starting_positions, starting_class_positions = (
            self.builder.get_starting_positions()
        )

        ctx = LeaderboardContext(
            drivers=drivers,
            positions=self.irsdk.get_value("CarIdxPosition") or [],
            class_positions=self.irsdk.get_value("CarIdxClassPosition") or [],
            starting_positions=starting_positions,
            starting_class_positions=starting_class_positions,
            last_lap_times=self.irsdk.get_value("CarIdxLastLapTime") or [],
            best_lap_times=self.irsdk.get_value("CarIdxBestLapTime") or [],
            laps_started=IRSDKService.normalize_laps(
                self.irsdk.get_value("CarIdxLap") or []
            ),
            lap_dist_pct=self.irsdk.get_value("CarIdxLapDistPct") or [],
            is_pitroad=self.irsdk.get_value("CarIdxOnPitRoad") or [],
            multiclass=CarClassComponent.is_multiclass(drivers),
            est_times=self.irsdk.get_value("CarIdxEstTime") or [],
            radio_transmit_car_idx=self.irsdk.get_value("RadioTransmitCarIdx"),
            player_idx=player_idx,
        )

        ctx.session_fastest_lap = self.lap_times.session_fastest_lap(ctx)
        ctx.class_fastest_laps = {
            class_id: self.lap_times.class_fastest_lap(ctx, class_id)
            for class_id in {driver.get("CarClassID") for driver in drivers}
        }
        ctx.irating_deltas = self._calculate_irating_deltas(ctx)
        ctx.sof = self._calculate_sof(ctx, player_idx)
        ctx.lap_deltas = self.lap_relation.compute(
            laps=ctx.laps_started,
            lap_dist_pct=ctx.lap_dist_pct,
            reference_idx=player_idx,
        )
        ctx.car_positions = self.build_car_positions(
            drivers=ctx.drivers,
            lap_dist_pct=ctx.lap_dist_pct,
            est_times=ctx.est_times,
        )
        self._record_track_time_line(ctx)
        ctx.track_time_line = self.track_time_line
        ctx.pit_labels = self._update_pit_stops(ctx)

        return ctx

    @staticmethod
    def build_car_positions(
        drivers: list[dict[str, Any]],
        lap_dist_pct: list[float],
        est_times: list[float],
    ) -> dict[int, CarPositionContext]:
        """
        Collect the track position of every car for the track components.

        Built once per snapshot from the telemetry arrays read in
        _build_context(), so the neighbors and the time line recording
        use the same values.

        Example:

            drivers      = [{"CarClassID": 4074, "CarClassEstLapTime": 230.72},
                            {"CarClassID": 4074, "CarClassEstLapTime": 232.76},
                            {"CarClassID": 2523, "CarClassEstLapTime": 211.4}]
            lap_dist_pct = [0.5, 0.62]
            est_times    = [115.36, 144.31]

            -> {
                0: CarPositionContext(0.5, 115.36, 230.72, 4074),
                1: CarPositionContext(0.62, 144.31, 232.76, 4074),
            }

            Car 2 has no telemetry yet and is left out.

        Args:
            drivers: DriverInfo.Drivers entries.
            lap_dist_pct: Lap distance by car index (CarIdxLapDistPct).
            est_times: Estimated time by car index (CarIdxEstTime).

        Returns:
            Track positions keyed by car index, for the cars present in all
            three sources.
        """
        count = min(len(drivers), len(lap_dist_pct), len(est_times))

        return {
            idx: CarPositionContext(
                lap_dist_pct=lap_dist_pct[idx],
                est_time=est_times[idx],
                est_lap_time=drivers[idx].get("CarClassEstLapTime"),
                class_id=drivers[idx].get("CarClassID"),
            )
            for idx in range(count)
        }

    def _record_track_time_line(self, ctx: LeaderboardContext) -> None:
        """
        Record the cars of the player's class into the player's time line.

        The time line is bound to the track, the player's class and the
        player's reference lap (cleared when any of them changes), then every
        car of the class on the track records its CarIdxEstTime; the time
        line rescales it to the player's car. Cars of another class, cars in
        the pits and the pace car are not recorded.

        Example:

            Player: Ferrari GT3 (class 4074, reference lap 230.72) at Le Mans.

            Ferrari GT3 (player)   -> recorded
            BMW GT3     (4074)     -> recorded, rescaled 232.76 -> 230.72
            Porsche GT3 (4074), in the pits     -> skipped
            LMP2        (2523)     -> skipped, another class
            Pace car               -> skipped

        Args:
            ctx: Leaderboard context of the current snapshot.

        Returns:
            None. Nothing is recorded without a valid player car.
        """
        player_idx = ctx.player_idx
        if player_idx is None or not 0 <= player_idx < len(ctx.drivers):
            return

        player_driver = ctx.drivers[player_idx]
        class_id = player_driver.get("CarClassID")
        weekend_info: dict[str, Any] = self.irsdk.get_value("WeekendInfo") or {}

        self.track_time_line.bind(
            track_id=weekend_info.get("TrackID"),
            class_id=class_id,
            est_lap_time=player_driver.get("CarClassEstLapTime"),
        )

        for idx, driver in enumerate(ctx.drivers):
            if driver.get("CarClassID") != class_id:
                continue
            if CarClassComponent.is_pace_car(driver):
                continue
            if idx < len(ctx.is_pitroad) and ctx.is_pitroad[idx]:
                continue

            car = ctx.car_positions.get(idx)
            if car is None:
                continue

            self.track_time_line.record(car)

    def _update_pit_stops(self, ctx: LeaderboardContext) -> dict[int, str]:
        """
        Update the pit stops of all cars and return their pit labels.

        Runs once per snapshot, so the pit stop state does not depend on how
        many times a car is built (the cars list and the neighbors build the
        same car). Pit stops of the previous session are cleared first.

        Example:

            Session 1, car 3 on the pit road on lap 5  -> {3: "IN L5"}
            Session changes to 2 (or restarts)         -> cleared -> {}

        Args:
            ctx: Leaderboard context of the current snapshot.

        Returns:
            Pit labels keyed by car index (see PitStopComponent.labels).
        """
        session_info: dict[str, Any] = self.irsdk.get_value("SessionInfo") or {}
        self._reset_pit_stops(session_info, self.irsdk.get_value("SessionTime"))

        now = time.time()
        self.pit_stops.update(
            laps_started=ctx.laps_started,
            is_pitroad=ctx.is_pitroad,
            now=now,
        )
        return self.pit_stops.labels(now)

    def _calculate_irating_deltas(self, ctx: LeaderboardContext) -> dict[int, int]:
        """
        Calculate iRating deltas from current leaderboard state.
        Returns mapping: UserID -> delta.
        """
        drivers = self.builder.get_irating_drivers(ctx)

        classes: dict[int, list[dict[str, Any]]] = {}

        for driver in drivers:
            if not driver["started"]:
                continue

            classes.setdefault(
                driver["class_id"],
                []
            ).append(driver)


        deltas: dict[int, int] = {}

        for class_id, class_drivers in classes.items():

            race_results = {
                driver["id"]: driver["irating"]
                for driver in class_drivers
            }

            class_deltas = self.irating_calculator.calculate(
                race_results
            )

            deltas.update(class_deltas)

        return {
            driver_id: delta
            for driver_id, delta in deltas.items()
        }

    def _calculate_sof(self, ctx: LeaderboardContext, player_idx: int) -> int:
        """Calculate Strength of Field for the active leaderboard class."""
        drivers = self.builder.get_irating_drivers(ctx)
        player_class_id = ctx.drivers[player_idx].get("CarClassID")

        race_results = {
            driver["id"]: driver["irating"]
            for driver in drivers
            if (not ctx.multiclass or driver["class_id"] == player_class_id)
        }
        return self.irating_calculator.calculate_sof(race_results)

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

    def _reset_pit_stops(
        self,
        session_info: dict,
        session_time: float | None,
    ) -> None:
        """Clear the pit stops when the session changes or restarts."""
        current_num = session_info.get("CurrentSessionNum", 0)

        session_changed = self._last_session_num != current_num
        session_restarted = (
            session_time is not None
            and self._last_session_time is not None
            and session_time < self._last_session_time
        )

        if session_changed or session_restarted:
            self.pit_stops.clear()

        self._last_session_num = current_num
        self._last_session_time = session_time

    def _get_current_session(self, session_info: dict) -> dict:
        """Return the current session dictionary from session info."""
        sessions = session_info.get("Sessions", [])
        current_num = session_info.get("CurrentSessionNum", 0)
        return sessions[current_num] if current_num < len(sessions) else {}
