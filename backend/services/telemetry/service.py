from dataclasses import dataclass
from typing import Any

from backend.services.base import BaseService
from backend.services.session_tracker import SessionKey, SessionTracker

# Pedal values above these thresholds count as braking / throttle application.
BRAKE_THRESHOLD = 0.05
THROTTLE_THRESHOLD = 0.05

@dataclass
class TelemetryContext:
    """
    Context container for telemetry related data.
    """

    throttle: float
    brake: float
    gear: int
    speed_ms: float
    is_brake_abs: bool


class TelemetryService(BaseService):
    """Business logic service working with telemetry data."""

    def __init__(self, irsdk_service):
        self.session_tracker = SessionTracker()
        super().__init__(irsdk_service, builder=None)
        self._reset_speed_metrics()

    def _build_context(self) -> TelemetryContext | None:
        """
        Returns TelemetryContext with up-to-date telemetry data.
        Overridden method from BaseService.
        """
        throttle: float = self.irsdk.get_value("Throttle")
        brake: float = self.irsdk.get_value("Brake")
        speed_ms: float = self.irsdk.get_speed_ms()
        gear: int = self.irsdk.get_value("Gear")
        is_brake_abs: bool = self.irsdk.get_value("BrakeABSactive")

        return TelemetryContext(
            throttle=self._normalize_pedal(throttle),
            brake=self._normalize_pedal(brake),
            gear=gear,
            speed_ms=speed_ms,
            is_brake_abs=is_brake_abs,
        )

    def _build_snapshot(self, ctx: TelemetryContext) -> dict[str, Any]:
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
        if self.session_tracker.is_changed(session_key):
            self._reset_speed_metrics()

        self._track_speed_metrics(ctx)

        return {
            "status": "ok",
            "throttle": ctx.throttle,
            "brake": ctx.brake,
            "throttle_pct": round(ctx.throttle * 100, 1),
            "brake_pct": round(ctx.brake * 100, 1),
            "gear": ctx.gear,
            "speed_ms": ctx.speed_ms,
            "top_speed_ms": self.top_speed_ms,
            "exit_speed_ms": self.exit_speed_ms,
            "is_brake_abs": ctx.is_brake_abs,
        }

    @staticmethod
    def _normalize_pedal(value: Any) -> float:
        """Return normalized pedal value in range [0.0, 1.0]."""
        if not isinstance(value, (int, float)):
            return 0.0
        return max(0.0, min(1.0, float(value)))

    def _reset_speed_metrics(self):
        """Clear Top Speed and Exit Speed tracking state."""
        self.top_speed_ms: float | None = None
        self.exit_speed_ms: float | None = None
        self._peak_speed_ms = 0.0
        self._is_braking = False
        self._is_exit_pending = False

    def _track_speed_metrics(self, ctx: TelemetryContext):
        """
        Update Top Speed and Exit Speed from the latest sample.

        Top Speed is the peak speed reached since the last brake release,
        latched when braking starts.
        Exit Speed is the speed at the first throttle application
        after braking ends.
        """
        if ctx.brake > BRAKE_THRESHOLD:
            if not self._is_braking:
                self._is_braking = True
                self.top_speed_ms = self._peak_speed_ms
            return

        if self._is_braking:
            self._is_braking = False
            self._peak_speed_ms = ctx.speed_ms
            self._is_exit_pending = True

        self._peak_speed_ms = max(self._peak_speed_ms, ctx.speed_ms)

        if self._is_exit_pending and ctx.throttle > THROTTLE_THRESHOLD:
            self.exit_speed_ms = ctx.speed_ms
            self._is_exit_pending = False
