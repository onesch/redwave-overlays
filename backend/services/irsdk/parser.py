import re

from backend.services.irsdk.service import IRSDKService
from backend.services.radar.parser import IRadarParser


class IRSDKParser(IRadarParser):
    """Parse and interpret iRacing telemetry values"""

    def __init__(self, service: IRSDKService):
        self.service = service

    def _clamp_percentage(self, value: float) -> int:
        """Clamp value to 0-100 percent"""
        return int(max(0, min(value * 100, 100)))

    def get_speed(self, speed_type: str) -> int | None:
        """Get speed in specified units"""
        speed_ms = self.service.get_value("Speed")
        if speed_ms is None:
            return None
        conversions = {"kmh": 3.6, "mph": 2.23694}
        factor = conversions.get(speed_type)
        if factor is None:
            return None
        return int(round(speed_ms * factor, 1))

    def get_throttle(self) -> int | None:
        """Get throttle percentage"""
        val = self.service.get_value("Throttle")
        if val is None:
            return None
        return self._clamp_percentage(val)

    def get_brake(self) -> int | None:
        """Get brake percentage"""
        val = self.service.get_value("BrakeRaw")
        if val is None:
            return None
        return self._clamp_percentage(val)

    def get_track_length_m(self, weekend_info: dict) -> float:
        """Parse track length from weekend info"""
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
        mult = {"km": 1000.0, "mi": 1609.344, "ft": 0.3048, "m": 1.0}.get(
            unit, 1.0
        )
        return val * mult
