from typing import Any
from dataclasses import dataclass

from backend.services.session_tracker import SessionKey, SessionTracker
from backend.services.base import (
    BaseService,
    BaseCarBuilder,
    SessionStateContext,
)
from backend.services.track_map.track_api import fetch_track_geometry


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
        self.session_tracker = SessionTracker()

        self._current_track_id: int | None = None
        self._current_track: dict | None = None

        super().__init__(irsdk_service, TrackMapCarBuilder())

    def _get_track(self, track_id: int) -> dict | None:
        """Returns cached geometry or fetches it when the track changes."""
        if track_id == self._current_track_id:
            print(f"[TrackMap] Cache hit: track_id={track_id}")
            return self._current_track

        print(
            f"[TrackMap] Track changed: "
            f"{self._current_track_id} -> {track_id}"
        )

        self._current_track_id = track_id

        print(f"[TrackMap] Fetching geometry for track_id={track_id}")
        geometry = fetch_track_geometry(track_id)

        if geometry is None:
            print(f"[TrackMap] Failed to fetch geometry: track_id={track_id}")
            self._current_track = None
        else:
            self._current_track = {"id": track_id, **geometry}
            print(
                f"[TrackMap] Geometry cached: "
                f"track_id={track_id}, "
                f"points={len(geometry['points'])}"
            )

        return self._current_track

    def _build_context(self) -> TrackMapContext | None:
        """
        Returns a TrackMapContext with up-to-date data.
        Overridden method from BaseService.
        """
        driver_info = self.irsdk.get_value("DriverInfo") or {}
        drivers = driver_info.get("Drivers", [])
        if not drivers:
            return None

        class_ids: set = {
            driver.get("CarClassID")
            for driver in drivers
            if driver.get("CarClassID")
        }
        multiclass: bool = len(class_ids) > 1

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
        player_idx: int = self.irsdk.get_value("PlayerCarIdx")
        weekend_info: dict[str, Any] = (
            self.irsdk.get_value("WeekendInfo") or {}
        )

        session_key = SessionKey(
            session_id=weekend_info.get("SessionID"),
            session_num=self.irsdk.get_value("SessionNum"),
        )
        is_session_changed = self.session_tracker.is_changed(session_key)

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
            "is_session_changed": is_session_changed,
            "multiclass": ctx.multiclass,
            "cars": cars,
            "track": self._get_track(weekend_info.get("TrackID")),
        }
