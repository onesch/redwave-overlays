from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from backend.database.data_loader import get_app_version, load_cards_data


templates = Jinja2Templates(directory="frontend/templates")
router = APIRouter()


@router.get("/main", response_class=HTMLResponse)
async def main_view(request: Request):
    app_version = get_app_version()
    return templates.TemplateResponse(
        "pages/main.html", {"request": request, "app_version": app_version}
    )


@router.get("/changelog", response_class=HTMLResponse)
async def changelog_view(request: Request):
    return templates.TemplateResponse(
        "pages/changelog.html", {"request": request}
    )


@router.get("/settings", response_class=HTMLResponse)
async def settings_view(request: Request):
    return templates.TemplateResponse(
        "pages/settings.html", {"request": request}
    )


@router.get("/overlays", response_class=HTMLResponse)
async def overlays_view(request: Request):
    cards = load_cards_data()
    return templates.TemplateResponse(
        "pages/overlays.html", {"request": request, "cards": cards}
    )
