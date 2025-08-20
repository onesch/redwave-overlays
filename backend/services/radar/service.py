from typing import Optional


RED_M = 4.5
YEL_M = 6.5
MAX_SHOW_DIST = 15.0
SIDE_WINDOW_M = 8.0

CLR_OFF = 0
CLR_CLEAR = 1
CLR_LEFT = 2
CLR_RIGHT = 3
CLR_BOTH = 4
CLR_TWO_LEFT = 5
CLR_TWO_RIGHT = 6


class RadarService:
    def __init__(self, irsdk_service):
        self.irsdk_service = irsdk_service


    def _severity_for_dist(self, dist: float | None) -> str:
        if dist is None:
            return "none"
        if dist <= RED_M:
            return "red"
        if dist <= YEL_M:
            return "yellow"
        return "ok"


    def _format_dist_meta(self, dist: float | None) -> tuple[Optional[float], str]:
        if dist is None:
            return None, "none"
        return dist, self._severity_for_dist(dist)


    def get_radar_json(self) -> dict:
        self.irsdk_service._ensure_connected()
        if not self.irsdk_service.is_connected():
            return {"reason": "not connected"}

        dist_ahead_raw = self.irsdk_service.get_value("CarDistAhead")
        dist_behind_raw = self.irsdk_service.get_value("CarDistBehind")
        clr = self.irsdk_service.get_value("CarLeftRight")
        left_present = clr in (CLR_LEFT, CLR_TWO_LEFT, CLR_BOTH)
        right_present = clr in (CLR_RIGHT, CLR_TWO_RIGHT, CLR_BOTH)

        weekend_info = self.irsdk_service.get_value("WeekendInfo")
        track_len_m = self.irsdk_service.get_track_length_m(weekend_info)
        if track_len_m <= 0:
            return {"reason": "track_len=0"}

        suppress_ahead = left_present or right_present
        if suppress_ahead:
            dist_ahead = None
            dist_behind = None
        else:
            dist_ahead = (
                dist_ahead_raw
                if 0 <= dist_ahead_raw <= MAX_SHOW_DIST
                else None
            )
            dist_behind = (
                dist_behind_raw
                if 0 <= dist_behind_raw <= MAX_SHOW_DIST
                else None
            )

        ahead_val, ahead_sev = self._format_dist_meta(dist_ahead)
        behind_val, behind_sev = self._format_dist_meta(dist_behind)

        return {
            "ahead_m": ahead_val,
            "ahead_severity": ahead_sev,
            "behind_m": behind_val,
            "behind_severity": behind_sev,
            "left": {"severity": "red"} if left_present else None,
            "right": {"severity": "red"} if right_present else None,
            "reason": "",
        }
