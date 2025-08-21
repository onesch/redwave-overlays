from fastapi import APIRouter

from backend.services.irsdk.parser import IRSDKParser
from backend.services.irsdk.service import IRSDKService
from backend.services.irsdk.schemas import IRSDKSchemas
from backend.services.radar.service import RadarService

router = APIRouter(prefix="/api")
irsdk_service = IRSDKService()
irsdk_parser = IRSDKParser(irsdk_service)
radar_service = RadarService(irsdk_service)


@router.get("/radar")
def get_radar_data():
    return radar_service.get_radar_json()


@router.get("/controls", response_model=IRSDKSchemas)
def get_controls_data():
    throttle = irsdk_parser.get_throttle()
    brake = irsdk_parser.get_brake()
    return IRSDKSchemas(throttle=throttle, brake=brake)
