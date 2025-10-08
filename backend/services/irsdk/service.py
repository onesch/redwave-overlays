import irsdk
from typing import Any


class IRSDKService():
    """Low level service to interact with iRacing SDK"""

    def __init__(self) -> None:
        self.ir = irsdk.IRSDK()
        self.started = False

    def _ensure_connected(self) -> tuple[bool, str]:
        """Ensure IRSDK connection is active"""
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
        """Check if IRSDK is connected"""
        return self.ir.is_initialized and self.ir.is_connected

    def get_value(self, field: str) -> Any | None:
        """Get any IRSDK field value"""
        if not self.is_connected():
            return None
        try:
            return self.ir[field]
        except KeyError:
            return None
