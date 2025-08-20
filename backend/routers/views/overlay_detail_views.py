from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from backend.database.data_loader import get_card_data_by_title, get_overlay_version


templates = Jinja2Templates(directory="frontend/templates")
router = APIRouter()


@router.get("/radar", response_class=HTMLResponse)
async def radar_detail_view(request: Request):
    card_data = get_card_data_by_title("Radar")
    radar_version = get_overlay_version("radar")
    return templates.TemplateResponse(
        "pages/card_detail/radar.html",
        {
            "request": request,
            "card_data": card_data,
            "radar_version": radar_version
        }
    )
