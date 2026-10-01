from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from backend.utils.templates import templates

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


@router.get("/track-map", response_class=HTMLResponse)
async def track_map_window_view(request: Request):
    return templates.TemplateResponse(
        request, "overlays/track_map.html"
    )


@router.get("/telemetry", response_class=RedirectResponse)
async def telemetry_window_view():
    return RedirectResponse(
        "/overlays/shared/baseOverlay.html?feature=telemetry"
    )
