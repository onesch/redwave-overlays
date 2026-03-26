from typing import Any
from dataclasses import dataclass

from backend.services.session_tracker import SessionKey, SessionTracker
from backend.services.base import (
    BaseService,
    BaseCarBuilder,
    SessionStateContext,
)
from backend.utils.track_url_generation import (
    DIRECTION_OVERRIDES,
    make_track_svg_url,
    fetch_svg,
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
        self.session_tracker = SessionTracker()
        self._cached_track_svg: str | None = None
        self._cached_start_finish_svg: str | None = None
        self._cached_track_id: int | None = None
        super().__init__(irsdk_service, TrackMapCarBuilder())

    def _update_track_svgs(
        self, track_id: str, track_name: str, track_short_name: str
    ):
        track_url = make_track_svg_url(
            track_id, track_name, track_short_name, svg_type="active"
        )
        start_finish_url = make_track_svg_url(
            track_id, track_name, track_short_name, svg_type="start-finish"
        )

        self._cached_track_svg = fetch_svg(track_url, extract_first=True)
        self._cached_start_finish_svg = fetch_svg(start_finish_url)
        self._cached_track_id = track_id

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

        track_id = weekend_info.get("TrackID")
        track_name = weekend_info.get("TrackName")
        track_short_name = weekend_info.get("TrackDisplayShortName")

        if is_session_changed or track_id != self._cached_track_id:
            self._update_track_svgs(track_id, track_name, track_short_name)

        return {
            "status": "ok",
            "player_id": player_idx,
            "is_session_changed": is_session_changed,
            "cars": cars,
            "track_svg": self._cached_track_svg,
            "start_finish_svg": self._cached_start_finish_svg,
            "direction_override": DIRECTION_OVERRIDES.get(track_id),
        }
