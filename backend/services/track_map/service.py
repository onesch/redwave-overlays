from typing import Any
from dataclasses import dataclass, field

from backend.components.car_class import CarClassComponent
from backend.components.lap_relation import LapRelationComponent
from backend.services.session_tracker import SessionKey, SessionTracker
from backend.services.base import (
    BaseService,
    BaseCarBuilder,
    SessionStateContext,
)
from backend.services.irsdk.service import IRSDKService
from backend.services.track_map.track_api import fetch_track_geometry
from backend.services.track_map.track_cache import (
    TRACK_CACHE_FILENAME,
    TrackGeometryCache,
)
from backend.utils.paths import get_user_data_path


@dataclass
class TrackMapContext(SessionStateContext):
    """
    Context container for track-map related data.

    Attributes:
        player_idx (int | None):
            Car index of the player.
        lap_deltas (dict[int, int]):
            Whole laps each car is ahead (positive) or behind (negative) of
            the player, keyed by car index (see LapRelationComponent).
    """

    player_idx: int | None = None
    lap_deltas: dict[int, int] = field(default_factory=dict)


class TrackMapCarBuilder(BaseCarBuilder):
    """
    Car builder for track-map visualization.
    """

    def build(self, idx: int, ctx: TrackMapContext) -> dict | None:
        """
        Extends base car data with class and lap relation data.
        """
        car = super().build(idx, ctx)
        if not car:
            return None
        # Specific fields
        driver = ctx.drivers[idx]
        car["class_id"] = driver.get("CarClassID")
        car["color"] = IRSDKService.get_class_color(
            driver.get("CarClassColor")
        )
        lap_delta = ctx.lap_deltas.get(idx)
        car["is_lap_ahead"] = LapRelationComponent.is_lap_ahead(lap_delta)
        car["is_lap_behind"] = LapRelationComponent.is_lap_behind(lap_delta)
        return car


class TrackMapService(BaseService):
    """Business logic service working with track-map data."""

    def __init__(self, irsdk_service):
        self.session_tracker = SessionTracker()

        self._current_track_id: int | None = None
        self._current_track: dict | None = None

        # Persistent geometry cache: survives app restarts.
        self._track_cache = TrackGeometryCache(
            get_user_data_path() / TRACK_CACHE_FILENAME
        )

        self.lap_relation = LapRelationComponent()

        super().__init__(irsdk_service, TrackMapCarBuilder())

    def _get_track(self, track_id: int | None) -> dict | None:
        """
        Returns the geometry of the current track. On a track change it
        is taken from the persistent cache, or fetched from the API
        (and cached) on a cache miss.
        """
        if track_id is None:
            return None

        if track_id == self._current_track_id:
            return self._current_track

        self._current_track_id = track_id

        geometry = self._track_cache.get(track_id)
        if geometry is None:
            geometry = fetch_track_geometry(track_id)

            if geometry is not None:
                self._track_cache.put(track_id, geometry)

        if geometry is None:
            self._current_track = None
        else:
            self._current_track = {"id": track_id, **geometry}

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

        multiclass: bool = CarClassComponent.is_multiclass(drivers)
        player_idx: int | None = self.irsdk.get_value("PlayerCarIdx")
        lap_dist_pct = self.irsdk.get_value("CarIdxLapDistPct") or []
        laps = IRSDKService.normalize_laps(
            self.irsdk.get_value("CarIdxLap") or []
        )

        return TrackMapContext(
            drivers=drivers,
            lap_dist_pct=lap_dist_pct,
            is_pitroad=self.irsdk.get_value("CarIdxOnPitRoad") or [],
            positions=self.irsdk.get_value("CarIdxPosition") or [],
            class_positions=self.irsdk.get_value("CarIdxClassPosition") or [],
            multiclass=multiclass,
            player_idx=player_idx,
            lap_deltas=self.lap_relation.compute(
                laps=laps,
                lap_dist_pct=lap_dist_pct,
                reference_idx=player_idx,
            ),
        )

    def _build_snapshot(self, ctx: TrackMapContext) -> dict[str, Any]:
        """
        Generates the snapshot for the API.
        Overridden method from BaseService.
        """
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
                    "class_id": car["class_id"],
                    "color": car["color"],
                    "is_lap_ahead": car["is_lap_ahead"],
                    "is_lap_behind": car["is_lap_behind"],
                }
            )
        return {
            "status": "ok",
            "player_id": ctx.player_idx,
            "is_session_changed": is_session_changed,
            "multiclass": ctx.multiclass,
            "cars": cars,
            "track": self._get_track(weekend_info.get("TrackID")),
        }
