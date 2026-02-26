from fastapi import APIRouter

from backend.services.irsdk.service import IRSDKService
from backend.services.radar.service import RadarService
from backend.services.leaderboard.service import Leaderboard
from backend.services.track_map.service import TrackMapService

router = APIRouter(prefix="/api")

irsdk_service = IRSDKService()
radar_service = RadarService(irsdk_service)
leaderboard_service = Leaderboard(irsdk_service)
track_map_service = TrackMapService(irsdk_service)


@router.get("/radar")
def get_radar_data():
    return radar_service.get_snapshot()


@router.get("/leaderboard")
def get_leaderboard_data():
    return leaderboard_service.get_leaderboard_snapshot()


@router.get("/track-map")
def get_track_map_data():
    return track_map_service.get_snapshot()
