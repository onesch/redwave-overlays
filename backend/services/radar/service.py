from typing import Optional, Tuple

from backend.services.radar.parser import IRadarParser
from backend.services.radar.constants import (
    RED_M,
    YEL_M,
    MAX_SHOW_DIST,
    CLR_LEFT,
    CLR_TWO_LEFT,
    CLR_BOTH,
    CLR_RIGHT,
    CLR_TWO_RIGHT,
)


class DistanceSeverity:
    """Encapsulates logic to calculate severity for distances."""

    @staticmethod
    def _sanitize_distance(dist: Optional[float]) -> Optional[float]:
        """Ignore distances outside valid range."""
        if dist is None or not (0 <= dist <= MAX_SHOW_DIST):
            return None
        return dist

    @staticmethod
    def for_distance(dist: Optional[float]) -> str:
        """Return severity level for a given distance."""
        if dist is None:
            return "none"
        if dist <= RED_M:
            return "red"
        if dist <= YEL_M:
            return "yellow"
        return "ok"

    @staticmethod
    def format_meta(dist: Optional[float]) -> Tuple[Optional[float], str]:
        """Return sanitized distance with severity."""
        sanitized_dist = DistanceSeverity._sanitize_distance(dist)
        return (sanitized_dist, DistanceSeverity.for_distance(sanitized_dist))


class RadarService:
    """Business logic service working with radar data."""

    def __init__(self, irsdk_service, parser: IRadarParser):
        self.irsdk_service = irsdk_service
        self.irsdk_parser = parser

    def get_radar_json(self) -> dict:
        """Build radar telemetry JSON response."""
        connected, reason = self.irsdk_service._ensure_connected()
        if not connected:
            return {"reason": reason}

        dist_ahead_raw = self.irsdk_service.get_value("CarDistAhead")
        dist_behind_raw = self.irsdk_service.get_value("CarDistBehind")
        clr = self.irsdk_service.get_value("CarLeftRight")
        weekend_info = self.irsdk_service.get_value("WeekendInfo")

        track_len_m = self.irsdk_parser.get_track_length_m(weekend_info)
        if track_len_m <= 0:
            return {"reason": "track_len=0"}

        left_present = clr in (CLR_LEFT, CLR_TWO_LEFT, CLR_BOTH)
        right_present = clr in (CLR_RIGHT, CLR_TWO_RIGHT, CLR_BOTH)
        suppress_ahead = left_present or right_present

        dist_ahead = None if suppress_ahead else dist_ahead_raw
        dist_behind = None if suppress_ahead else dist_behind_raw

        ahead_val, ahead_sev = DistanceSeverity.format_meta(dist_ahead)
        behind_val, behind_sev = DistanceSeverity.format_meta(dist_behind)

        return {
            "ahead_m": ahead_val,
            "ahead_severity": ahead_sev,
            "behind_m": behind_val,
            "behind_severity": behind_sev,
            "left": {"severity": "red"} if left_present else None,
            "right": {"severity": "red"} if right_present else None,
            "reason": "",
        }
