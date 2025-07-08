from pydantic import BaseModel
from typing import Optional


class IRSDKSchemas(BaseModel):
    speed: Optional[int] = None
    throttle: Optional[int] = None
    brake: Optional[int] = None


"""
    @property
    def speed_kmh(self) -> Optional[float]:
        if self.speed is None:
            return None
        return round(self.speed * 3.6, 1)


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
