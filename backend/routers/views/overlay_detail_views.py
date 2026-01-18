from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from backend.database.data_loader import get_card_data_by_title
from backend.utils.templates import templates

router = APIRouter()


@router.get("/radar", response_class=HTMLResponse)
async def radar_detail_view(request: Request):
    card_data = get_card_data_by_title("Radar")
    return templates.TemplateResponse(
        "pages/card_detail/radar.html",
        {
            "request": request,
            "card_data": card_data,
        },
    )

@router.get("/leaderboard", response_class=HTMLResponse)
async def leaderboard_detail_view(request: Request):
    card_data = get_card_data_by_title("Leaderboard")
    return templates.TemplateResponse(
        "pages/card_detail/leaderboard.html",
        {
            "request": request,
            "card_data": card_data,
        },
    )
