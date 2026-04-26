from dataclasses import dataclass
from typing import Any

from backend.services.base import BaseService


@dataclass
class TelemetryContext:
    """
    Context container for telemetry related data.
    """

    throttle: float
    brake: float
    gear: int
    speed_km: float
    is_brake_abs: bool


class TelemetryService(BaseService):
    """Business logic service working with telemetry data."""

    def __init__(self, irsdk_service):
        super().__init__(irsdk_service, builder=None)

    def _build_context(self) -> TelemetryContext | None:
        self.irsdk._ensure_connected()

        throttle: float = self.irsdk.get_value("Throttle")
        brake: float = self.irsdk.get_value("Brake")
        speed_km: float = self.irsdk.get_speed_kmh()
        gear: int = self.irsdk.get_value("Gear")
        is_brake_abs: bool = self.irsdk.get_value("BrakeABSactive")

        return TelemetryContext(
            throttle=self._normalize_pedal(throttle),
            brake=self._normalize_pedal(brake),
            gear=gear,
            speed_km=speed_km,
            is_brake_abs=is_brake_abs,
        )

    def _build_snapshot(self, ctx: TelemetryContext) -> dict[str, Any]:
        return {
            "status": "ok",
            "throttle": ctx.throttle,
            "brake": ctx.brake,
            "throttle_pct": round(ctx.throttle * 100, 1),
            "brake_pct": round(ctx.brake * 100, 1),
            "gear": ctx.gear,
            "speed_km": ctx.speed_km,
            "is_brake_abs": ctx.is_brake_abs,
        }

    @staticmethod
    def _normalize_pedal(value: Any) -> float:
        """Return normalized pedal value in range [0.0, 1.0]."""
        if not isinstance(value, (int, float)):
            return 0.0
        return max(0.0, min(1.0, float(value)))
