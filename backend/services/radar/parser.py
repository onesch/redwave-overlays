from typing import Protocol, Any


class IRadarParser(Protocol):
    """
    interface/Protocol for Radar service, which
    requires only part of IRSDKParser functionality.

    RadarService -> IRadarParser (requires only part)
    -> IRSDKParser -> IRSDKService -> irsdk.IRSDK
    """

    def get_track_length_m(self, weekend_info: Any) -> float: ...
