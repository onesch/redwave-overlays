from fastapi import APIRouter

from backend.services.irsdk.parser import IRSDKParser
from backend.services.irsdk.service import IRSDKService
from backend.services.leaderboard.service import Leaderboard
from backend.services.radar.service import RadarService

router = APIRouter(prefix="/api")
irsdk_service = IRSDKService()
irsdk_parser = IRSDKParser(irsdk_service)
radar_service = RadarService(irsdk_service, irsdk_parser)
leaderboard_service = Leaderboard(irsdk_service)


@router.get("/radar")
def get_radar_data():
    return radar_service.get_radar_json()


@router.get("/leaderboard")
def get_leaderboard_data():
    snapshot = leaderboard_service.get_leaderboard_snapshot()
    return snapshot
