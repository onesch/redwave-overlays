from typing import Protocol, Any


class IRadarParser(Protocol):
    """Abstract interface for Radar data extraction"""

    def get_track_length_m(self, weekend_info: Any) -> float: ...
