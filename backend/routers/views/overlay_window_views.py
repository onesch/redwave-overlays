from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from backend.utils.templates import templates

router = APIRouter()


@router.get("/radar", response_class=HTMLResponse)
async def radar_window_view(request: Request):
    return templates.TemplateResponse(
        request, "overlays/radar.html"
    )


@router.get("/leaderboard", response_class=HTMLResponse)
async def leaderboard_window_view(request: Request):
    return templates.TemplateResponse(
        request, "overlays/leaderboard.html"
    )


@router.get("/track-map", response_class=HTMLResponse)
async def track_map_window_view(request: Request):
    return templates.TemplateResponse(
        request, "overlays/track_map.html"
    )


@router.get("/telemetry", response_class=HTMLResponse)
async def telemetry_window_view(request: Request):
    return templates.TemplateResponse(
        request, "overlays/telemetry.html"
    )
