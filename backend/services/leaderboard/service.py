import time
from typing import Any, Dict, List, Optional

# Constant for offline races: in a RACE session, if the race is lap-based, the API returns this "magic" value.
LAP_RACE_API_PLACEHOLDER: float = 86400.0


class TimeFormatter:
    """Utility for formatting lap times."""

    @staticmethod
    def format_lap_time(seconds: float | None) -> str:
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
    def format_session_time(secs: float, is_seconds: bool) -> str:
        """Format session time from seconds to 'HH:MM:SS' or 'MM:SS' format."""
        if secs is None or secs < 0:
            return "--:--.---"

        hrs = int(secs // 3600)
        mins = int((secs % 3600) // 60)
        secs_remain = int(secs % 60)

        if is_seconds:
            if hrs > 0:
                return f"{hrs:02d}:{mins:02d}:{secs_remain:02d}h"
            return f"{mins:02d}:{secs_remain:02d}m"
        else:
            if hrs > 0:
                return f"{hrs:02d}:{mins:02d}h"
            return f"{hrs:02d}:{mins:02d}m"


class CarDataBuilder:
    """Responsible for constructing car data entries."""

    def __init__(self, irsdk_service):
        self.irsdk = irsdk_service

    def _get_starting_position(
        self, car_idx: int, field: str, offset: int
    ) -> int:
        """Get a starting position from qualification results."""
        session_info = self.irsdk.get_value("SessionInfo") or {}
        sessions = session_info.get("Sessions") or []

        for sess in sessions:
            session_type = sess.get("SessionType")
            if session_type in ("Warmup", "Lone Qualify", "Open Qualify"):
                for res in sess.get("ResultsPositions") or []:
                    if res.get("CarIdx") == car_idx:
                        # The API returns ClassPosition from zero,
                        # so offset=1 is needed.
                        return int(res.get(field, 0)) + offset
        return 0

    def build(
        self,
        idx: int,
        drivers: List[dict],
        positions: List[int],
        class_positions: List[int],
        last_lap_times: List[float],
        laps_started: List[int],
        lap_dist_pct: List[float],
        multiclass: bool,
    ) -> Optional[Dict[str, Any]]:
        """Generates driver data for the leaderboard."""
        driver = drivers[idx]
        name = driver.get("UserName", "")
        if name.upper() == "PACE CAR":
            return None

        pos_list = class_positions if multiclass else positions
        pos = int(pos_list[idx] or 0)

        if pos == -1:
            pos = None
        if pos == 0:
            pos = self._get_starting_position(
                car_idx=idx,
                field="ClassPosition" if multiclass else "Position",
                offset=1 if multiclass else 0,
            )

        last_lap = TimeFormatter.format_lap_time(last_lap_times[idx])
        laps = int(laps_started[idx] or 0)
        if laps < 0:
            laps = 0

        dist = lap_dist_pct[idx]
        first_name = (name.strip().split() or [""])[0]

        return {
            "pos": pos,
            "car_idx": idx,
            "car_number": driver.get("CarNumber"),
            "name": first_name,
            "laps_started": laps,
            "last_lap": last_lap,
            "irating": driver.get("IRating"),
            "license": driver.get("LicString"),
            "car_class_color": driver.get("CarClassColor"),
            "lap_dist_pct": (
                round(dist, 3)
                if isinstance(dist, (int, float)) and dist >= 0
                else None
            ),
        }


class CarSorter:
    """Sort cars by position, keeping None or 0 at the end."""

    @staticmethod
    def sort(cars: List[Dict[str, int | None]]) -> List[Dict[str, int | None]]:
        return sorted(
            cars,
            key=lambda c: (
                c["pos"] is None or c["pos"] == 0,
                c["pos"] if isinstance(c["pos"], int) else 9999,
            ),
        )


class Leaderboard:
    """Main service for building leaderboard telemetry data."""

    def __init__(self, irsdk_service):
        self.irsdk = irsdk_service
        self.builder = CarDataBuilder(irsdk_service)

    def _is_multiclass(self, drivers: list) -> bool:
        """Check if race contains multiple car classes."""
        class_ids = {
            d.get("CarClassID") for d in drivers if d.get("CarClassID")
        }
        return len(class_ids) > 1

    def get_leaderboard_snapshot(self) -> Dict[str, Any]:
        """Return a snapshot of leaderboard data with player context."""
        self.irsdk._ensure_connected()

        positions = self.irsdk.get_value("CarIdxPosition") or []
        class_positions = self.irsdk.get_value("CarIdxClassPosition") or []
        laps_started = self.irsdk.get_value("CarIdxLap") or []
        player_idx = self.irsdk.get_value("PlayerCarIdx")
        last_lap_times = self.irsdk.get_value("CarIdxLastLapTime") or []
        lap_dist_pct = self.irsdk.get_value("CarIdxLapDistPct") or []
        drivers = (self.irsdk.get_value("DriverInfo") or {}).get("Drivers", [])

        if not drivers or player_idx is None:
            return {"error": "No driver/player data"}

        multiclass = self._is_multiclass(drivers)

        cars = [
            car
            for idx in range(len(drivers))
            if idx != player_idx
            and (
                car := self.builder.build(
                    idx,
                    drivers,
                    positions,
                    class_positions,
                    last_lap_times,
                    laps_started,
                    lap_dist_pct,
                    multiclass,
                )
            )
        ]

        cars_sorted = CarSorter.sort(cars)
        player_car = self.builder.build(
            player_idx,
            drivers,
            positions,
            class_positions,
            last_lap_times,
            laps_started,
            lap_dist_pct,
            multiclass,
        )

        neighbors = self._get_neighbors(player_idx, drivers, lap_dist_pct)
        leaderboard_data = self._get_session_info(player_idx)

        return {
            "cars": cars_sorted,
            "player": player_car,
            "neighbors": neighbors,
            "leaderboard_data": leaderboard_data,
            "multiclass": multiclass,
            "timestamp": int(time.time()),
        }

    def _get_neighbors(self, player_idx: int, drivers: list, lap_dist_pct: list[float]):
        """Return 3 cars ahead and 3 behind with gap in percent and seconds."""
        my_dist = lap_dist_pct[player_idx]
        if not isinstance(my_dist, (int, float)) or my_dist < 0:
            return {"ahead": [], "behind": []}

        lap_times = self.irsdk.get_value("CarIdxLastLapTime") or []
        my_lap_time = (
            lap_times[player_idx] if player_idx < len(lap_times) else None
        )

        if not my_lap_time or my_lap_time <= 0:
            my_lap_time = (
                (self.irsdk.get_value("DriverInfo") or {})
                .get("Drivers", [{}])[player_idx]
                .get("CarClassEstLapTime")
            )

        is_multiclass = self._is_multiclass(drivers)
        positions = self.irsdk.get_value("CarIdxPosition") or []
        class_positions = self.irsdk.get_value("CarIdxClassPosition") or []
        laps_started = self.irsdk.get_value("CarIdxLap") or []
        candidates_ahead, candidates_behind = [], []

        for idx, dist in enumerate(lap_dist_pct):
            if (
                idx == player_idx
                or not isinstance(dist, (int, float))
                or dist < 0
                or idx >= len(drivers)
            ):
                continue

            gap_pct = (dist - my_dist) % 1.0
            gap_sec = gap_pct * my_lap_time

            car_data = self.builder.build(
                idx,
                drivers,
                positions,
                class_positions,
                lap_times,
                laps_started,
                lap_dist_pct,
                is_multiclass,
            )

            if not car_data:
                continue
            lap_diff = laps_started[idx] - laps_started[player_idx]
            pct_diff = abs(dist - my_dist)

            if lap_diff > 0:
                car_data["lap_status"] = "ahead_lap"
            elif lap_diff < 0:
                car_data["lap_status"] = "behind_lap"
            else:
                car_data["lap_status"] = None

            if 0 < gap_pct <= 0.5:
                candidates_ahead.append(
                    {"car": car_data, "gap_pct": gap_pct, "gap_sec": gap_sec, "lap_status": car_data["lap_status"]}
                )
            elif gap_pct > 0.5:
                candidates_behind.append(
                    {
                        "car": car_data,
                        "gap_pct": gap_pct - 1.0,
                        "gap_sec": (gap_pct - 1.0) * my_lap_time,
                        "lap_status": car_data["lap_status"]
                    }
                )


        candidates_ahead.sort(key=lambda x: x["gap_pct"])
        candidates_behind.sort(key=lambda x: x["gap_pct"], reverse=True)

        ahead = [
            {
                **c["car"],
                "gap_pct": round(c["gap_pct"], 3),
                "gap_sec": round(abs(c["gap_sec"]), 2),
            }
            for c in candidates_ahead[:3]
        ]
        behind = [
            {
                **c["car"],
                "gap_pct": round(abs(c["gap_pct"]), 3),
                "gap_sec": round(abs(c["gap_sec"]), 2),
            }
            for c in candidates_behind[:3]
        ]

        return {"ahead": ahead, "behind": behind}

    def _is_lap_race(self, session_time: str | float | None) -> bool:
        if session_time is None:
            return False

        try:
            val = float(session_time)
            if val >= LAP_RACE_API_PLACEHOLDER:
                return True
        except (ValueError, TypeError):
            s = str(session_time).lower()
            if "unlimited" in s:
                return True
            if "sec" in s:
                try:
                    val_sec = float(s.split()[0])
                    if val_sec == LAP_RACE_API_PLACEHOLDER:
                        return True
                except ValueError:
                    return False
        return False

    def _get_player_lap_time(self, player_idx: int, sessions: list) -> Optional[float]:
        fastest_time = None

        for sess in sessions:
            for record in sess.get("ResultsFastestLap", []) or []:
                if (
                    record.get("CarIdx") == player_idx
                    and record.get("FastestTime", -1) > 0
                ):
                    fastest_time = record["FastestTime"]

        driver = (self.irsdk.get_value("DriverInfo") or {}).get("Drivers", [])[player_idx]
        est_lap_time = driver.get("CarClassEstLapTime")

        return fastest_time if fastest_time is not None else est_lap_time

    def _resolve_session_time(
        self,
        current_session: dict,
        player_lap_time: float,
        session_time_str: str | float,
        format: bool = True,
    ) -> str | float | None:
        """
        Resolve session time. Returns formatted string by default or float seconds if format=False.
        """
        session_type = current_session.get("SessionType", "").upper()
        approx = False
        result: float | str | None = None

        if session_type == "RACE":
            if self._is_lap_race(session_time_str):
                session_laps = current_session.get("SessionLaps")
                if isinstance(session_laps, int) and session_laps > 0 and player_lap_time and player_lap_time > 0:
                    result = session_laps * player_lap_time
                    approx = True
            elif isinstance(session_time_str, str) and "sec" in session_time_str:
                result = float(session_time_str.split()[0])
                approx = True

        if result is None:
            try:
                result = float(session_time_str)
            except (ValueError, TypeError):
                result = None

        if format and result is not None:
            formatted = TimeFormatter.format_session_time(result, is_seconds=False)
            if approx:
                formatted = f"~{formatted}"
            return formatted
        return result

    def _get_session_info(self, player_idx: int) -> Dict[str, Any]:
        """Extract relevant session & timing info, considering all sessions."""
        session_info = self.irsdk.get_value("SessionInfo") or {}
        sessions = session_info.get("Sessions", [])
        current_session_num = session_info.get("CurrentSessionNum", 0)
        current = sessions[current_session_num] if 0 <= current_session_num < len(sessions) else {}

        session_laps = current.get("SessionLaps")
        session_time_current = self.irsdk.get_value("SessionTime")
        session_time_total = self.irsdk.get_value("SessionTimeTotal")

        player_lap_time = self._get_player_lap_time(player_idx, sessions)
        resolved_session_time_current = TimeFormatter.format_session_time(session_time_current, is_seconds=True)
        resolved_session_time = self._resolve_session_time(
            current, player_lap_time, session_time_total, format=False
        )
        resolved_session_time_formatted = self._resolve_session_time(
            current, player_lap_time, session_time_total, format=True
        )
        return {
            "session_laps": session_laps,
            "player_lap_time": player_lap_time,
            "session_time_current": resolved_session_time_current,
            "session_time": resolved_session_time,
            "session_time_formatted": resolved_session_time_formatted,
        }
