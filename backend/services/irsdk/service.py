import irsdk
from typing import Any


class IRSDKService():
    """Low level service to interact with iRacing SDK."""

    def __init__(self) -> None:
        self.ir = irsdk.IRSDK()
        self.started = False

    def _ensure_connected(self) -> tuple[bool, str]:
        """Ensure IRSDK connection is active."""
        if not self.started:
            self.ir.startup()
            self.started = True
        elif not self.ir.is_connected:
            self.ir.shutdown()
            self.ir.startup()

        if not getattr(self.ir, "is_connected", False):
            return False, "not connected"
        if not getattr(self.ir, "is_initialized", True):
            return False, "not initialized"
        return True, ""

    def is_connected(self) -> bool:
        """Check if IRSDK is connected."""
        return self.ir.is_initialized and self.ir.is_connected

    def get_value(self, field: str) -> Any | None:
        """Get any IRSDK field value."""
        if not self.is_connected():
            return None
        try:
            return self.ir[field]
        except KeyError:
            return None

    @staticmethod
    def get_car_rgb(
        *,
        idx: int,
        drivers: list[dict],
        player_idx: int | None,
        multiclass: bool,
    ) -> str:
        """Return the car's color as RGB string."""
        if idx >= len(drivers):
            return "#1b2a3a"

        if idx == player_idx:
            return "#1e6cff"

        rgb = drivers[idx].get("CarClassColor")

        if not multiclass or rgb in (None, 0xFFFFFF):
            return "#1b2a3a"

        r = (rgb >> 16) & 0xFF
        g = (rgb >> 8) & 0xFF
        b = rgb & 0xFF
        return f"rgb({r},{g},{b})"

    def get_car_location(self) -> str:
        """Return 'track' if player is on track, 'garage' otherwise."""
        is_on_track: bool = self.get_value("IsOnTrack")
        return "track" if is_on_track else "garage"
