from fastapi import APIRouter
from fastapi.responses import RedirectResponse

router = APIRouter()


@router.get("/radar", response_class=RedirectResponse)
async def radar_window_view():
    return RedirectResponse(
        "/overlays/shared/baseOverlay.html?feature=radar"
    )


@router.get("/leaderboard", response_class=RedirectResponse)
async def leaderboard_window_view():
    return RedirectResponse(
        "/overlays/shared/baseOverlay.html?feature=leaderboard"
    )


@router.get("/track-map", response_class=RedirectResponse)
async def track_map_window_view():
    return RedirectResponse(
        "/overlays/shared/baseOverlay.html?feature=track-map"
    )


@router.get("/telemetry", response_class=RedirectResponse)
async def telemetry_window_view():
    return RedirectResponse(
        "/overlays/shared/baseOverlay.html?feature=telemetry"
    )
