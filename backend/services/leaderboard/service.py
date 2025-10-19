import time


class Leaderboard:
    """Business logic service working with leaderboard data"""

    def __init__(self, irsdk_service):
        self.irsdk_service = irsdk_service

    @staticmethod
    def format_lap_time(seconds):
        """Get formatted (--:--.---) last lap time"""
        if seconds is None or seconds <= 0:
            return "--:--.---"
        ms = int(seconds * 1000)
        s = ms // 1000
        ms_remain = ms % 1000
        m = s // 60
        s = s % 60
        return f"{m:02d}:{s:02d}.{ms_remain:03d}"

    @staticmethod
    def _normalize_laps_started(laps: int) -> int:
        """Replaces -1 with 0, otherwise as is"""
        return 0 if laps < 0 else laps

    def _get_starting_position(self, car_idx: int) -> int:
        """Get a starting position from the qualification results"""
        session_info = self.irsdk_service.get_value("SessionInfo") or {}
        sessions = session_info.get("Sessions") or []

        for sess in sessions:
            session_type = sess.get("SessionType")

            if session_type in ("Lone Qualify", "Open Qualify"):
                for res in sess.get("ResultsPositions") or []:
                    if res.get("CarIdx") == car_idx:
                        return int(res.get("Position", 0))
        return 0

    def get_leaderboard_snapshot(self):
        """Build leaderboard telemetry JSON response."""
        self.irsdk_service._ensure_connected()

        positions = self.irsdk_service.get_value("CarIdxPosition") or []
        laps_started = self.irsdk_service.get_value("CarIdxLap") or []
        player_idx = self.irsdk_service.get_value("PlayerCarIdx")
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
            words = name.strip().split()
            first_name = words[0] if words else ""

            # фильтр Pace Car
            if name.upper() == "PACE CAR":
                return None

            # основная позиция
            pos = int(safe_get(positions, idx, 0) or 0)
            if pos == -1:
                pos = None

            if pos == 0:
                pos = self._get_starting_position(idx)

            last_lap = self.format_lap_time(safe_get(last_lap_times, idx, 0))
            laps = self._normalize_laps_started(
                int(safe_get(laps_started, idx, 0) or 0)
            )
            dist = safe_get(lap_dist_pct, idx, -1.0)

            return {
                "pos": pos,
                "car_idx": int(idx),
                "car_number": driver.get("CarNumber"),
                "name": first_name,
                "laps_started": laps,
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
        cars_sorted = sorted(
            cars,
            key=lambda c: (
                c["pos"] is None or c["pos"] == 0,
                c["pos"] if isinstance(c["pos"], int) else 9999
            )
        )

        # Данные игрока
        player_car = build_car(int(player_idx))
        player_data = player_car

        # Соседи по прогрессу круга - 3 впереди и 3 позади
        my_dist = safe_get(lap_dist_pct, player_idx, -1.0)
        ahead_cars = []
        behind_cars = []

        if isinstance(my_dist, (int, float)) and my_dist >= 0:
            ahead_candidates = []
            behind_candidates = []
            
            for idx in range(len(drivers)):
                if idx == player_idx:
                    continue
                other_dist = safe_get(lap_dist_pct, idx, -1.0)
                if not isinstance(other_dist, (int, float)) or other_dist < 0:
                    continue
                
                # Calculate gap in lap percentage
                gap = (other_dist - my_dist) % 1.0
                
                car_data = build_car(idx)
                if car_data:
                    # Cars ahead have gap between 0 and 0.5
                    if 0 < gap <= 0.5:
                        ahead_candidates.append({
                            'car': car_data,
                            'gap': gap
                        })
                    # Cars behind have gap between 0.5 and 1.0 (convert to negative)
                    elif gap > 0.5:
                        behind_candidates.append({
                            'car': car_data,
                            'gap': gap - 1.0  # Convert to negative value
                        })
            
            ahead_candidates.sort(key=lambda x: x['gap'])
            behind_candidates.sort(key=lambda x: x['gap'], reverse=True)

            for candidate in ahead_candidates[:3]:
                ahead_cars.append({
                    **candidate['car'],
                    'gap_pct': round(candidate['gap'], 3)
                })

            for candidate in behind_candidates[:3]:
                behind_cars.append({
                    **candidate['car'],
                    'gap_pct': round(abs(candidate['gap']), 3)  # Convert to positive for display
                })

        neighbors = {
            "ahead": ahead_cars,
            "behind": behind_cars,
        }
        session_info = self.irsdk_service.get_value("SessionInfo")
        current_session_number = session_info.get("CurrentSessionNum")
        current_session = session_info.get("Sessions")[current_session_number]
        session_laps = current_session.get("SessionLaps")

        session_time_sec = None
        session_time_str = current_session.get("SessionTime")
        if session_time_str and "sec" in session_time_str:
            try:
                session_time_sec = float(session_time_str.split()[0])
            except ValueError:
                session_time_sec = None

        # оценка времени круга для игрока
        driver = drivers[player_idx]
        est_lap_time = driver.get("CarClassEstLapTime")

        # проверяем реальные быстрые круги из SessionInfo
        fastest_time = None
        results_fastest = current_session.get("ResultsFastestLap", [])
        for f in results_fastest:
            if f.get("CarIdx") == player_idx and f.get("FastestTime", -1) > 0:
                fastest_time = f["FastestTime"]
                break

        # используем реальный быстрый круг, если есть
        car_est_lap_time = fastest_time or est_lap_time

        leaderboard_data = {
            "session_laps": session_laps,
            "session_time": session_time_sec,
            "car_est_lap_time": car_est_lap_time,
        }

        snapshot = {
            "cars": cars_sorted,
            "player": player_data,
            "neighbors": neighbors,
            "leaderboard_data": leaderboard_data,
            "timestamp": int(time.time()),
        }
        return snapshot
