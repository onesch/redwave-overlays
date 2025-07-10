from fastapi import APIRouter

from backend.services.irsdk_service.service import IRSDKService
from backend.services.irsdk_service.schemas import IRSDKSchemas

router = APIRouter()
irsdk_service = IRSDKService()


@router.get("/api/speed", response_model=IRSDKSchemas)
def get_speed_data():
    speed = irsdk_service.get_speed("kmh")
    return IRSDKSchemas(speed=speed)


@router.get("/api/controls", response_model=IRSDKSchemas)
def get_controls_data():
    throttle = irsdk_service.get_throttle()
    brake = irsdk_service.get_brake()
    return IRSDKSchemas(throttle=throttle, brake=brake)
