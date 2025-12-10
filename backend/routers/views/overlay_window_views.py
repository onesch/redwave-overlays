from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates


templates = Jinja2Templates(directory="frontend/templates")
router = APIRouter()


@router.get("/radar", response_class=HTMLResponse)
async def radar_window_view(request: Request):
    return templates.TemplateResponse(
        "overlays/radar.html", {"request": request}
    )


@router.get("/leaderboard", response_class=HTMLResponse)
async def leaderboard_window_view(request: Request):
    return templates.TemplateResponse(
        "overlays/leaderboard.html", {"request": request}
    )
