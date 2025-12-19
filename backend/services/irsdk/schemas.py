from pydantic import BaseModel
from typing import Optional


class IRSDKSchemas(BaseModel):
    speed: Optional[int] = None
    throttle: Optional[int] = None
    brake: Optional[int] = None
