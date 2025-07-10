from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

templates = Jinja2Templates(directory="frontend/templates")
router = APIRouter()


@router.get("/main_window", response_class=HTMLResponse)
async def main_window_view(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@router.get("/speed", response_class=HTMLResponse)
async def speed_view(request: Request):
    return templates.TemplateResponse("overlays/speed.html", {"request": request})


@router.get("/controls", response_class=HTMLResponse)
async def controls_view(request: Request):
    return templates.TemplateResponse("overlays/controls.html", {"request": request})
