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
