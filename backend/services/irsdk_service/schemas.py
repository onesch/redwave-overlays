from pydantic import BaseModel, field_validator
from typing import Optional


class IRSDKSchemas(BaseModel):
    speed: Optional[int] = None
    throttle: Optional[int] = None
    brake: Optional[int] = None


    @field_validator('speed', mode='before')
    def convert_speed_to_int(cls, v):
        if v is None:
            return None
        return int(round(v))


    @field_validator('throttle', 'brake', mode='before')
    def convert_to_percent(cls, v):
        if v is None:
            return None
        # Ожидаем, что v от 0 до 1, переводим в проценты
        return int(round(v * 100))

"""
    @property
    def speed_kmh(self) -> Optional[float]:
        if self.speed is None:
            return None
        return round(self.speed * 3.6, 1)


    @property
    def speed_mph(self) -> Optional[float]:
        if self.speed is None:
            return None
        return round(self.speed * 2.23694, 1)


    @property
    def throttle_percent(self) -> Optional[int]:
        return int(self.throttle * 100) if self.throttle is not None else None


    @property
    def brake_percent(self) -> Optional[int]:
        return int(self.brake * 100) if self.brake is not None else None
"""