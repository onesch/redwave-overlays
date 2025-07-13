from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

templates = Jinja2Templates(directory="frontend/templates")
router = APIRouter()


@router.get("/main", response_class=HTMLResponse)
async def main_view(request: Request):
    return templates.TemplateResponse("pages/main.html", {"request": request})


@router.get("/foo", response_class=HTMLResponse)
async def foo_view(request: Request):
    return templates.TemplateResponse("pages/foo.html", {"request": request})


@router.get("/settings", response_class=HTMLResponse)
async def settings_view(request: Request):
    return templates.TemplateResponse("pages/settings.html", {"request": request})


@router.get("/speed", response_class=HTMLResponse)
async def speed_view(request: Request):
    return templates.TemplateResponse("overlays/speed.html", {"request": request})


@router.get("/controls", response_class=HTMLResponse)
async def controls_view(request: Request):
    return templates.TemplateResponse("overlays/controls.html", {"request": request})
