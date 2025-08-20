import irsdk
import re
from typing import Any


class IRSDKService:
    def __init__(self):
        self.ir = irsdk.IRSDK()
        self.started = False


    def _ensure_connected(self):
        if not self.started:
            self.ir.startup()
            self.started = True
        elif not self.ir.is_connected:
            self.ir.shutdown()
            self.ir.startup()


    def is_connected(self) -> bool:
        return self.ir.is_initialized and self.ir.is_connected


    def get_value(self, field: str) -> Any | None:
        """
        Универсальный метод получения значения.
        """
        if not self.is_connected():
            return None
        try:
            return self.ir[field]
        except KeyError:
            return None


    def get_track_length_m(self, weekend_info) -> float:
        if not isinstance(weekend_info, dict):
            return 0.0
        tl = weekend_info.get("TrackLength", "")
        if not tl:
            return 0.0
        m = re.match(r"\s*([\d\.]+)\s*(km|mi|m|ft)?", tl, re.IGNORECASE)
        if not m:
            return 0.0
        val = float(m.group(1))
        unit = (m.group(2) or "m").lower()
        mult = {"km": 1000.0, "mi": 1609.344, "ft": 0.3048, "m": 1.0}.get(unit, 1.0)
        return val * mult


    def get_speed(self, speed_type: str) -> int | None:
        speed_ms = self.get_value("Speed")
        if speed_ms is None:
            return None

        if speed_type == "kmh":
            speed = int(round(speed_ms * 3.6, 1))
        elif speed_type == "mph":
            speed = int(round(speed_ms * 2.23694, 1))
        else:
            speed = None

        return speed


    def get_throttle(self) -> int | None:
        throttle = self.get_value("Throttle")
        if throttle is None:
            return None
        throttle_percent = int(max(0, min(throttle * 100, 100)))
        return throttle_percent


    def get_brake(self) -> int | None:
        brake = self.get_value("BrakeRaw")
        if brake is None:
            return None
        brake_percent = int(max(0, min(brake * 100, 100)))
        return brake_percent
