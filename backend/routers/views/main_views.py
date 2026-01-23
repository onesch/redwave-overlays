from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path

from backend.database.data_loader import (
    get_app_version,
    load_cards_data,
    get_overlays_card_data,
)
from backend.utils.templates import templates

router = APIRouter()


@router.get("/main", response_class=HTMLResponse, name="main")
async def main_view(request: Request):
    app_version = get_app_version()
    return templates.TemplateResponse(
        "pages/main.html", {"request": request, "app_version": app_version}
    )


@router.get("/changelog", response_class=HTMLResponse, name="changelog")
async def changelog_view(request: Request):
    images_dir = Path("frontend/static/images/changelog_versions")
    images = [f"images/changelog_versions/{f.name}" for f in images_dir.glob("*.png")]
    images.sort()
    return templates.TemplateResponse(
        "pages/changelog.html", {"request": request, "images": images}
    )


@router.get("/settings", response_class=HTMLResponse, name="settings")
async def settings_view(request: Request):
    return templates.TemplateResponse("pages/settings.html", {"request": request})


@router.get("/overlays", response_class=HTMLResponse)
async def overlays(request: Request, overlay: str | None = None):
    overlays_list, selected_overlay, card_data = get_overlays_card_data(overlay)
    return templates.TemplateResponse(
        "pages/overlays.html",
        {
            "request": request,
            "overlays": overlays_list,
            "selected_overlay": selected_overlay,
            "card_data": card_data,
        },
    )
