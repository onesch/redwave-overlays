from dataclasses import dataclass
from typing import Any


@dataclass
class SessionStateContext:
    """
    Immutable container with session-related session data.

    Attributes:
        drivers (list[dict]):
            Raw driver info from iRacing (DriverInfo.Drivers).
        positions (list[int]):
            Overall race positions by car index.
        class_positions (list[int]):
            Class positions by car index.
        lap_dist_pct (list[float]):
            Lap distance percentage for each car.
        is_pitroad (list[bool]):
            Whether the car is currently on pit road.
        multiclass (bool):
            Whether the session contains multiple car classes.

    Used by BaseService implementations to pass pre-fetched,
    consistent data into snapshot builders.
    """
    drivers: list[dict]
    positions: list[int]
    class_positions: list[int]
    lap_dist_pct: list[float]
    is_pitroad: list[bool]
    multiclass: bool


class BaseCarBuilder:
    """
    Base builder responsible for constructing per-car data
    from a SessionStateContext.

    Intended to be subclassed by services that require
    additional car-specific fields.
    """
    def build(self, idx: int, ctx: SessionStateContext) -> dict | None:
        """
        Build a base representation of a car.
        """
        driver = ctx.drivers[idx]
        if self._is_pace_car(driver):
            return None

        return {
            "car_idx": idx,
            "car_number": driver.get("CarNumber"),
            "lap_dist_pct": ctx.lap_dist_pct[idx],
            "is_in_pitroad": ctx.is_pitroad[idx],
        }

    @staticmethod
    def _is_pace_car(driver: dict) -> bool:
        """Checks if a car is a pace car by name."""
        return driver.get("UserName", "").upper() == "PACE CAR"


class BaseService:
    """
    Base service implementing the snapshot lifecycle.

    Template method pattern:
        - build context
        - build snapshot
        - return empty snapshot if context is unavailable
    """
    def __init__(self, irsdk_service, builder: BaseCarBuilder | None):
        self.irsdk = irsdk_service
        self.builder = builder

    def get_snapshot(self) -> dict[str, Any]:
        """
        Public entry point for retrieving service data.
        """
        ctx = self._build_context()
        if not ctx:
            return self._empty_snapshot()
        return self._build_snapshot(ctx)

    def _build_context(self):
        """
        Collect and validate session data.
        """
        raise NotImplementedError

    def _build_snapshot(self, ctx) -> dict:
        """
        Build the snapshot using prepared context.
        """
        raise NotImplementedError

    def _empty_snapshot(self) -> dict:
        """
        Return a default snapshot when data is unavailable.
        """
        return {"status": "waiting", "cars": []}
