from dataclasses import dataclass
from typing import Any

from backend.services.base import BaseService
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


@dataclass
class RadarContext:
    """
    Immutable container with radar-related telemetry data.

    Attributes:
        dist_ahead (float | None):
            Distance to the car ahead in meters.
            None if not available or suppressed.
        dist_behind (float | None):
            Distance to the car behind in meters.
            None if not available or suppressed.
        car_left_right (int):
            Indicator of cars on the left or right sides.
            Used to determine side alerts
            (e.g., CLR_LEFT, CLR_RIGHT, CLR_BOTH).

    Used by RadarService to pass pre-fetched, consistent telemetry data
    into snapshot builders.
    """
    dist_ahead: float | None
    dist_behind: float | None
    car_left_right: int


class DistanceSeverity:
    """Utility class responsible for classifying distance severity."""

    @staticmethod
    def _sanitize_distance(dist: float | None) -> float | None:
        """Ignore distances outside valid range."""
        if dist is None or not (0 <= dist <= MAX_SHOW_DIST):
            return None
        return dist

    @staticmethod
    def for_distance(dist: float | None) -> str:
        """Return severity level for a given distance."""
        if dist is None:
            return "none"
        if dist <= RED_M:
            return "red"
        if dist <= YEL_M:
            return "yellow"
        return "ok"

    @staticmethod
    def format_meta(dist: float | None) -> tuple[float | None, str]:
        """Return sanitized distance with severity."""
        sanitized_dist = DistanceSeverity._sanitize_distance(dist)
        return (sanitized_dist, DistanceSeverity.for_distance(sanitized_dist))


class RadarService(BaseService):
    """Business logic service working with radar data."""

    def __init__(self, irsdk_service):
        super().__init__(irsdk_service, builder=None)

    def _build_context(self) -> RadarContext | None:
        """
        Returns RadarContext with up-to-date radar telemetry.
        Overridden method from BaseService.
        """
        self.irsdk._ensure_connected()

        car_left_right = self.irsdk.get_value("CarLeftRight")
        if car_left_right is None:
            return None

        return RadarContext(
            dist_ahead=self.irsdk.get_value("CarDistAhead"),
            dist_behind=self.irsdk.get_value("CarDistBehind"),
            car_left_right=car_left_right,
        )

    def _build_snapshot(self, ctx: RadarContext) -> dict[str, Any]:
        """
        Generates the snapshot for the API.
        Overridden method from BaseService.
        """
        left_present = ctx.car_left_right in (
            CLR_LEFT, CLR_TWO_LEFT, CLR_BOTH
        )
        right_present = ctx.car_left_right in (
            CLR_RIGHT, CLR_TWO_RIGHT, CLR_BOTH
        )

        suppress_ahead = left_present or right_present

        dist_ahead = None if suppress_ahead else ctx.dist_ahead
        dist_behind = None if suppress_ahead else ctx.dist_behind

        ahead_val, ahead_sev = DistanceSeverity.format_meta(dist_ahead)
        behind_val, behind_sev = DistanceSeverity.format_meta(dist_behind)

        return {
            "status": "ok",
            "ahead_m": ahead_val,
            "ahead_severity": ahead_sev,
            "behind_m": behind_val,
            "behind_severity": behind_sev,
            "left": {"severity": "red"} if left_present else None,
            "right": {"severity": "red"} if right_present else None,
        }
