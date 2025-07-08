from typing import Any
import irsdk


class IRSDKService:
    def __init__(self):
        self.ir = irsdk.IRSDK()
        self.ir.startup()


    def is_connected(self) -> bool:
        return self.ir.is_initialized


    def get_value(self, field: str) -> Any | None:
        if not self.is_connected():
            return None
        try:
            value = self.ir[field]
        except KeyError:
            return None
        return value


    def get_speed(self, speed_type: str) -> int | None:
        speed_ms = self.get_value("Speed")
        if speed_ms is None:
            return None

        if speed_type == "kmh":
            speed = int(round(speed_ms * 3.6, 1))
        elif speed_type == "mph":
            speed = int(round(speed_ms * 2.23694, 1))
        else:
            speed = None

        return speed


    def get_throttle(self) -> int | None:
        throttle = self.get_value("Throttle")
        if throttle is None:
            return None
        throttle_percent = int(max(0, min(throttle * 100, 100)))
        return throttle_percent


    def get_brake(self) -> int | None:
        brake = self.get_value("BrakeRaw")
        if brake is None:
            return None
        brake_percent = int(max(0, min(brake * 100, 100)))
        return brake_percent
