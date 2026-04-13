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


class TelemetryService(BaseService):
    """Business logic service working with telemetry data."""

    def __init__(self, irsdk_service):
        super().__init__(irsdk_service, builder=None)

    def _build_context(self) -> TelemetryContext | None:
        self.irsdk._ensure_connected()

        throttle = self.irsdk.get_value("Throttle")
        brake = self.irsdk.get_value("Brake")

        if throttle is None and brake is None:
            return None

        return TelemetryContext(
            throttle=self._sanitize_value(throttle),
            brake=self._sanitize_value(brake),
        )

    def _build_snapshot(self, ctx: TelemetryContext) -> dict[str, Any]:
        return {
            "status": "ok",
            "throttle": ctx.throttle,
            "brake": ctx.brake,
            "throttle_pct": round(ctx.throttle * 100, 1),
            "brake_pct": round(ctx.brake * 100, 1),
        }

    @staticmethod
    def _sanitize_value(value: Any) -> float:
        if not isinstance(value, (int, float)):
            return 0.0
        return max(0.0, min(1.0, float(value)))
