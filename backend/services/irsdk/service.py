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
    def is_pace_car(driver: dict) -> bool:
        """
        Check if a DriverInfo.Drivers entry is the pace car.

        :param driver: driver entry from DriverInfo.Drivers.
        :return: True if flagged by CarIsPaceCar or named "Pace Car".
        """
        return bool(driver.get("CarIsPaceCar")) or (
            driver.get("UserName", "").upper() == "PACE CAR"
        )

    @staticmethod
    def is_multiclass(drivers: list[dict]) -> bool:
        """
        Check if the session has more than one car class.

        The pace car is ignored: it has its own class id.

        :param drivers: DriverInfo.Drivers entries.
        :return: True if more than one CarClassID is present.
        """
        class_ids = {
            driver.get("CarClassID")
            for driver in drivers
            if driver.get("CarClassID")
            and not IRSDKService.is_pace_car(driver)
        }
        return len(class_ids) > 1

    @staticmethod
    def normalize_laps(raw_laps: list[Any]) -> list[int]:
        """
        Normalize lap counts by car index (CarIdxLap).

        Negative values, non-integers and None are treated as 0.

        :param raw_laps: the CarIdxLap value.
        :return: lap counts with invalid values replaced by 0.
        """
        return [
            lap if isinstance(lap, int) and lap >= 0 else 0
            for lap in raw_laps
        ]

    @staticmethod
    def get_class_color(rgb: Any) -> str | None:
        """
        Decode an iRacing CarClassColor (0xRRGGBB integer) to '#rrggbb'.

        :param rgb: the CarClassColor value of a driver entry.
        :return: the color, or None if the class has no color.
        """
        # White (0xFFFFFF) stands for "no class color", as in the leaderboard.
        if not isinstance(rgb, int) or rgb == 0xFFFFFF:
            return None
        return f"#{rgb:06x}"

    def get_car_location(self) -> str:
        """Return 'track' if player is on track, 'garage' otherwise."""
        is_on_track: bool = self.get_value("IsOnTrack")
        return "track" if is_on_track else "garage"

    def get_speed_ms(self) -> float:
        """Get vehicle speed in m/s, the unit reported by iRacing."""
        speed = self.get_value("Speed")
        if speed is None:
            return 0.0
        try:
            return float(speed)
        except (TypeError, ValueError):
            return 0.0
