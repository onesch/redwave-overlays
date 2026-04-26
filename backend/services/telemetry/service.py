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


class TelemetryService(BaseService):
    """Business logic service working with telemetry data."""

    def __init__(self, irsdk_service):
        super().__init__(irsdk_service, builder=None)

    def _build_context(self) -> TelemetryContext | None:
        self.irsdk._ensure_connected()

        throttle = self.irsdk.get_value("Throttle")
        brake = self.irsdk.get_value("Brake")
        speed_km = self.irsdk.get_speed_kmh()
        gear = self.irsdk.get_value("Gear")
        if not isinstance(gear, int):
            gear = 0

        return TelemetryContext(
            throttle=self._normalize_pedal(throttle),
            brake=self._normalize_pedal(brake),
            gear=gear,
            speed_km=speed_km,
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
        }

    @staticmethod
    def _normalize_pedal(value: Any) -> float:
        """Return normalized pedal value in range [0.0, 1.0]."""
        if not isinstance(value, (int, float)):
            return 0.0
        return max(0.0, min(1.0, float(value)))
