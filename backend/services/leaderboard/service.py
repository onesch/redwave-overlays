import time


class Leaderboard:
    """Business logic service working with leaderboard data"""

    def __init__(self, irsdk_service):
        self.irsdk_service = irsdk_service

    @staticmethod
    def format_lap_time(seconds):
        """Get formated(--:--.---) last lap time"""
        if seconds is None or seconds <= 0:
            return "--:--.---"
        ms = int(seconds * 1000)
        s = ms // 1000
        ms_remain = ms % 1000
        m = s // 60
        s = s % 60
        return f"{m:02d}:{s:02d}.{ms_remain:03d}"

    @staticmethod
    def _normalize_laps_completed(laps: int) -> int:
        """Replaces -1 with 0, otherwise as is"""
        return 0 if laps < 0 else laps

    @staticmethod
    def _normalize_total_laps(total: int) -> int:
        """32767 (unlimited) → 0, otherwise as is"""
        return 0 if total == 32767 else total

    def get_leaderboard_snapshot(self):
        """Build leaderboard telemetry JSON response."""
        self.irsdk_service._ensure_connected()
        if not self.irsdk_service.is_connected():
            return {"error": "No connection to iRacing"}

        positions = self.irsdk_service.get_value("CarIdxPosition") or []
        laps_completed = self.irsdk_service.get_value("CarIdxLapCompleted") or []
        player_idx = self.irsdk_service.get_value("PlayerCarIdx")
        total_laps = self.irsdk_service.get_value("SessionLapsTotal") or 0
        last_lap_times = self.irsdk_service.get_value("CarIdxLastLapTime") or []
        lap_dist_pct = self.irsdk_service.get_value("CarIdxLapDistPct") or []
        drivers = (self.irsdk_service.get_value("DriverInfo") or {}).get("Drivers", [])

        if not drivers or player_idx is None:
            return {"error": "No driver/player data"}

        def safe_get(seq, idx, default=None):
            return seq[idx] if (seq and 0 <= idx < len(seq)) else default

        def build_car(idx: int):
            driver = drivers[idx]
            name = driver.get("UserName") or ""
            # фильтр Pace Car
            if name.upper() == "PACE CAR":
                return None

            pos = int(safe_get(positions, idx, 0) or 0)
            last_lap = self.format_lap_time(safe_get(last_lap_times, idx, 0))
            laps = self._normalize_laps_completed(
                int(safe_get(laps_completed, idx, 0) or 0)
            )
            dist = safe_get(lap_dist_pct, idx, -1.0)
            return {
                "pos": pos,
                "car_idx": int(idx),
                "car_number": driver.get("CarNumber"),
                "name": name.split()[0] if name else "",
                "laps_completed": laps,
                "last_lap": last_lap,
                "irating": driver.get("IRating"),
                "license": driver.get("LicString"),
                "lap_dist_pct": (
                    round(dist, 3)
                    if (isinstance(dist, (int, float)) and dist >= 0)
                    else None
                ),
            }

        # Собираем все машины (даже с pos == 0), кроме Pace Car
        cars = []
        for car_idx in range(len(drivers)):
            if car_idx == player_idx:
                continue
            car = build_car(car_idx)
            if car is not None:
                cars.append(car)

        # Сортировка по pos для общего списка
        cars_sorted = sorted(cars, key=lambda c: (c["pos"] == 0, c["pos"]))

        # Данные игрока
        player_car = build_car(int(player_idx))
        player_data = player_car or {
            "pos": int(safe_get(positions, player_idx, 0) or 0),
            "car_idx": int(player_idx),
            "name": "",
            "car_number": None,
            "last_lap": self.format_lap_time(safe_get(last_lap_times, player_idx, 0)),
            "laps_completed": self._normalize_laps_completed(
                int(safe_get(laps_completed, player_idx, 0) or 0)
            ),
            "irating": None,
            "license": None,
            "lap_dist_pct": None,
        }

        # Соседи по прогрессу круга
        my_dist = safe_get(lap_dist_pct, player_idx, -1.0)
        ahead = None
        behind = None
        best_ahead = 1.1
        best_behind = 1.1

        if isinstance(my_dist, (int, float)) and my_dist >= 0:
            for idx in range(len(drivers)):
                if idx == player_idx:
                    continue
                other_dist = safe_get(lap_dist_pct, idx, -1.0)
                if not isinstance(other_dist, (int, float)) or other_dist < 0:
                    continue

                # расстояние вперёд по кругу [0..1)
                forward = (other_dist - my_dist) % 1.0
                if 1e-9 < forward < best_ahead:
                    best_ahead = forward
                    ahead = build_car(idx)

                # расстояние назад по кругу [0..1)
                backward = (my_dist - other_dist) % 1.0
                if 1e-9 < backward < best_behind:
                    best_behind = backward
                    behind = build_car(idx)

        neighbors = {
            "ahead": (dict(ahead, gap_pct=round(best_ahead, 3)) if ahead else None),
            "behind": (dict(behind, gap_pct=round(best_behind, 3)) if behind else None),
        }

        leaderboard_data = {
            "total_laps": self._normalize_total_laps(int(total_laps)),
        }

        snapshot = {
            "cars": cars_sorted,
            "player": player_data,
            "neighbors": neighbors,
            "leaderboard_data": leaderboard_data,
            "timestamp": int(time.time()),
        }

        return snapshot
