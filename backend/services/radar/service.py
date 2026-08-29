from typing import Any

from backend.services.base import BaseService
from backend.services.radar.context import RadarContext
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

        return (
            sanitized_dist,
            DistanceSeverity.for_distance(sanitized_dist),
        )


class RadarService(BaseService):
    """Business logic service working with radar data."""

    def __init__(self, irsdk_service):
        super().__init__(irsdk_service, builder=None)

    def _build_context(self) -> RadarContext | None:
        """
        Returns RadarContext with up-to-date radar telemetry.
        Overridden method from BaseService.
        """
        car_left_right = self.irsdk.get_value("CarLeftRight")
        if car_left_right is None:
            return None

        weekend_info = self.irsdk.get_value("WeekendInfo") or {}

        track_length_m = self._parse_track_length(weekend_info.get("TrackLength"))

        return RadarContext(
            dist_ahead=self.irsdk.get_value("CarDistAhead"),
            dist_behind=self.irsdk.get_value("CarDistBehind"),
            car_left_right=car_left_right,
            lap_dist_pct=self.irsdk.get_value("CarIdxLapDistPct") or [],
            player_idx=self.irsdk.get_value("PlayerCarIdx"),
            track_length_m=track_length_m,
        )

    @staticmethod
    def _parse_track_length(track_length: str | None) -> float | None:
        """
        Convert iRacing TrackLength from kilometers to meters.

        Example:
            "3.9927 km" -> 3992.7
        """
        if not track_length:
            return None

        try:
            value = float(track_length.split()[0])
        except (ValueError, IndexError):
            return None

        return value * 1000

    def _build_snapshot(
        self,
        ctx: RadarContext,
    ) -> dict[str, Any]:
        """
        Generates the snapshot for the API.
        Overridden method from BaseService.
        """
        left_data, right_data = self._build_side_data(ctx)

        suppress_ahead = (
            left_data is not None or right_data is not None
        )

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
            "left": left_data,
            "right": right_data,
        }

    def _build_side_data(
        self, ctx: RadarContext,
    ) -> tuple[dict | None, dict | None]:
        """
        Returns data for left and right side indicators
        based on radar context.
        """
        left_present = ctx.car_left_right in (
            CLR_LEFT,
            CLR_TWO_LEFT,
            CLR_BOTH,
        )
        right_present = ctx.car_left_right in (
            CLR_RIGHT,
            CLR_TWO_RIGHT,
            CLR_BOTH,
        )
        left_data = None
        right_data = None

        # Note: When both sides are present,
        # _compute_side_offset is called twice.
        # This is intentional because offset is
        # ignored on the frontend when bothSides is true.

        if left_present:
            left_data = self._compute_side_offset(ctx)

        if right_present:
            right_data = self._compute_side_offset(ctx)

        return left_data, right_data

    @staticmethod
    def _lap_delta(my: float, other: float) -> float:
        """
        Computes the normalized lap distance delta between two cars,
        accounting for wrap-around at 0/1.

        Returns:
            Positive value if the other car is ahead.
            Negative value if the other car is behind.
            Zero if both cars are aligned.
        """
        delta = other - my

        if delta > 0.5:
            delta -= 1.0
        elif delta < -0.5:
            delta += 1.0

        return delta

    def _find_closest_side_car(self, ctx: RadarContext) -> int | None:
        """
        Returns the index of the closest car on the side
        based on lap distance percentage.
        """
        my_idx = ctx.player_idx
        if my_idx is None:
            return None

        my_pct = ctx.lap_dist_pct[my_idx]

        best_idx = None
        best_score = float("inf")

        for i, pct in enumerate(ctx.lap_dist_pct):
            if i == my_idx:
                continue

            if pct is None:
                continue

            delta = abs(self._lap_delta(my_pct, pct))

            if delta < best_score:
                best_score = delta
                best_idx = i

        return best_idx

    def _compute_side_offset(self, ctx: RadarContext) -> dict | None:
        """
        Computes the longitudinal offset of the closest side car.
        The lap distance percentage is converted to meters using
        the current track length.

        Example:

            Track length = 4000 m
            Player = 0.45
            Other car = 0.452

            delta_pct = 0.002

            offset_m = 0.002 * 4000 = 8 m

        Result:

            {"offset_m": 8.0}
        """

        if ctx.player_idx is None:
            return None

        if ctx.track_length_m is None:
            return None

        my_pct = ctx.lap_dist_pct[ctx.player_idx]

        car_idx = self._find_closest_side_car(ctx)
        if car_idx is None:
            return None

        other_pct = ctx.lap_dist_pct[car_idx]

        delta_pct = self._lap_delta(my_pct, other_pct)

        offset_m = delta_pct * ctx.track_length_m

        return {
            "offset_m": round(offset_m, 2),
        }
