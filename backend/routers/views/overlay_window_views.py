from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates


templates = Jinja2Templates(directory="frontend/templates")
router = APIRouter()


@router.get("/radar", response_class=HTMLResponse)
async def radar_window_view(request: Request):
    return templates.TemplateResponse("overlays/radar.html", {"request": request})


@router.get("/controls", response_class=HTMLResponse)
async def controls_window_view(request: Request):
    return templates.TemplateResponse("overlays/controls.html", {"request": request})
