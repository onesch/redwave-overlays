import time
from typing import Any, Dict, List, Optional


class TimeFormatter:
    """Utility for formatting lap times."""

    DEFAULT_TIME = "--:--.---"

    @staticmethod
    def format(seconds: Optional[float]) -> str:
        """Convert lap time in seconds to formatted string."""
        if seconds is None or seconds <= 0:
            return TimeFormatter.DEFAULT_TIME
        ms = int(seconds * 1000)
        s = ms // 1000
        ms_remain = ms % 1000
        m = s // 60
        s = s % 60
        return f"{m:02d}:{s:02d}.{ms_remain:03d}"


class CarDataBuilder:
    """Responsible for constructing car data entries."""

    def __init__(self, irsdk_service):
        self.irsdk = irsdk_service

    def _get_starting_position(self, car_idx: int) -> int:
        """Get a starting position from the qualification results"""
        session_info = self.irsdk.get_value("SessionInfo") or {}
        sessions = session_info.get("Sessions") or []

        for sess in sessions:
            session_type = sess.get("SessionType")

            if session_type in ("Warmup", "Lone Qualify", "Open Qualify"):
                for res in sess.get("ResultsPositions") or []:
                    if res.get("CarIdx") == car_idx:
                        return int(res.get("Position", 0))
        return 0

    def build(
        self,
        idx: int,
        drivers: list,
        positions: list,
        last_lap_times: list,
        laps_started: list,
        lap_dist_pct: list,
    ):
        driver = drivers[idx]
        name = driver.get("UserName", "")
        if name.upper() == "PACE CAR":
            return None

        pos = int(positions[idx] or 0)
        if pos == -1:
            pos = None
        elif pos == 0:
            pos = self._get_starting_position(idx)

        last_lap = TimeFormatter.format(last_lap_times[idx])
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
            "lap_dist_pct": round(dist, 3) if isinstance(dist, (int, float)) and dist >= 0 else None,
        }


class CarSorter:
    """Sort cars by position, keeping None or 0 at the end."""

    @staticmethod
    def sort(cars: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
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

    def get_leaderboard_snapshot(self) -> Dict[str, Any]:
        """Return a snapshot of leaderboard data with player context."""
        self.irsdk._ensure_connected()

        positions = self.irsdk.get_value("CarIdxPosition") or []
        laps_started = self.irsdk.get_value("CarIdxLap") or []
        player_idx = self.irsdk.get_value("PlayerCarIdx")
        last_lap_times = self.irsdk.get_value("CarIdxLastLapTime") or []
        lap_dist_pct = self.irsdk.get_value("CarIdxLapDistPct") or []
        drivers = (self.irsdk.get_value("DriverInfo") or {}).get("Drivers", [])

        if not drivers or player_idx is None:
            return {"error": "No driver/player data"}

        cars = [
            car
            for idx in range(len(drivers))
            if idx != player_idx
            and (car := self.builder.build(
                idx, drivers, positions, last_lap_times, laps_started, lap_dist_pct
            ))
        ]

        cars_sorted = CarSorter.sort(cars)
        player_car = self.builder.build(
            player_idx, drivers, positions, last_lap_times, laps_started, lap_dist_pct
        )

        neighbors = self._get_neighbors(player_idx, drivers, lap_dist_pct)
        leaderboard_data = self._get_session_info(player_idx)

        return {
            "cars": cars_sorted,
            "player": player_car,
            "neighbors": neighbors,
            "leaderboard_data": leaderboard_data,
            "timestamp": int(time.time()),
        }

    def _get_neighbors(self, player_idx, drivers, lap_dist_pct):
        """Return 3 cars ahead and 3 behind based on lap distance."""
        my_dist = lap_dist_pct[player_idx]
        if not isinstance(my_dist, (int, float)) or my_dist < 0:
            return {"ahead": [], "behind": []}

        candidates_ahead, candidates_behind = [], []

        for idx, dist in enumerate(lap_dist_pct):
            if idx == player_idx or not isinstance(dist, (int, float)) or dist < 0:
                continue

            gap = (dist - my_dist) % 1.0
            car_data = self.builder.build(
                idx,
                drivers,
                self.irsdk.get_value("CarIdxPosition"),
                self.irsdk.get_value("CarIdxLastLapTime"),
                self.irsdk.get_value("CarIdxLap"),
                lap_dist_pct,
            )
            if not car_data:
                continue

            if 0 < gap <= 0.5:
                candidates_ahead.append({"car": car_data, "gap": gap})
            elif gap > 0.5:
                candidates_behind.append({"car": car_data, "gap": gap - 1.0})

        candidates_ahead.sort(key=lambda x: x["gap"])
        candidates_behind.sort(key=lambda x: x["gap"], reverse=True)

        ahead = [
            {**c["car"], "gap_pct": round(c["gap"], 3)}
            for c in candidates_ahead[:3]
        ]
        behind = [
            {**c["car"], "gap_pct": round(abs(c["gap"]), 3)}
            for c in candidates_behind[:3]
        ]

        return {"ahead": ahead, "behind": behind}

    def _get_session_info(self, player_idx):
        """Extract relevant session and timing info, considering all sessions."""
        session_info = self.irsdk.get_value("SessionInfo") or {}
        sessions = session_info.get("Sessions", [])
        current_session_num = session_info.get("CurrentSessionNum", 0)
        current = sessions[current_session_num] if 0 <= current_session_num < len(sessions) else {}

        session_laps = current.get("SessionLaps")
        session_time_str = current.get("SessionTime")
        session_time_sec = None
        if session_time_str and "sec" in session_time_str:
            session_time_sec = float(session_time_str.split()[0])

        fastest_time = None
        for sess in sessions:
            for record in sess.get("ResultsFastestLap", []) or []:
                if record.get("CarIdx") == player_idx and record.get("FastestTime", -1) > 0:
                    fastest_time = record["FastestTime"] if fastest_time is None else min(fastest_time, record["FastestTime"])

        if fastest_time is None:
            for sess in sessions:
                for record in sess.get("ResultsFastestLap", []) or []:
                    if record.get("FastestTime", -1) > 0:
                        fastest_time = record["FastestTime"] if fastest_time is None else min(fastest_time, record["FastestTime"])

        driver = (self.irsdk.get_value("DriverInfo") or {}).get("Drivers", [])[player_idx]
        est_lap_time = driver.get("CarClassEstLapTime")

        return {
            "session_laps": session_laps,
            "session_time": session_time_sec,
            "player_lap_time": fastest_time or est_lap_time,
        }
