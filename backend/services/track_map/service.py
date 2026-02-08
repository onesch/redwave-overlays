from typing import Any
from dataclasses import dataclass

from backend.services.base import (
    BaseService,
    BaseCarBuilder,
    SessionStateContext,
)


@dataclass
class TrackMapContext(SessionStateContext):
    """
    Context container for track-map related data.
    """
    pass


class TrackMapCarBuilder(BaseCarBuilder):
    """
    Car builder for track-map visualization.
    """
    def build(self, idx: int, ctx: TrackMapContext) -> dict | None:
        """
        Extends base car data with class-specific data.
        """
        car = super().build(idx, ctx)
        if not car:
            return None
        # Specific fields
        car["car_class_color"] = ctx.drivers[idx].get("CarClassColor")
        return car


class TrackMapService(BaseService):
    """Business logic service working with track-map data."""

    def __init__(self, irsdk_service):
        super().__init__(irsdk_service, TrackMapCarBuilder())

    def _build_context(self) -> TrackMapContext | None:
        """
        Returns a TrackMapContext with up-to-date data.
        Overridden method from BaseService.
        """
        self.irsdk._ensure_connected()

        driver_info = self.irsdk.get_value("DriverInfo") or {}
        drivers = driver_info.get("Drivers", [])
        if not drivers:
            return None

        multiclass = (
            len({d.get("CarClassID") for d in drivers if d.get("CarClassID")})
            > 1
        )

        return TrackMapContext(
            drivers=drivers,
            lap_dist_pct=self.irsdk.get_value("CarIdxLapDistPct") or [],
            is_pitroad=self.irsdk.get_value("CarIdxOnPitRoad") or [],
            positions=self.irsdk.get_value("CarIdxPosition") or [],
            class_positions=self.irsdk.get_value("CarIdxClassPosition") or [],
            multiclass=multiclass,
        )

    def _build_snapshot(self, ctx: TrackMapContext) -> dict[str, Any]:
        """
        Generates the snapshot for the API.
        Overridden method from BaseService.
        """
        player_idx = self.irsdk.get_value("PlayerCarIdx")
        cars = []

        for idx in range(len(ctx.drivers)):
            car = self.builder.build(idx, ctx)
            if not car:
                continue
            cars.append(
                {
                    "player_id": idx,
                    "car_number": car["car_number"],
                    "lap_dist_pct": car["lap_dist_pct"],
                    "color": self.irsdk.get_car_rgb(
                        idx=idx,
                        drivers=ctx.drivers,
                        player_idx=player_idx,
                        multiclass=ctx.multiclass,
                ),
                }
            )

        return {
            "status": "ok",
            "player_id": player_idx,
            "cars": cars,
        }
