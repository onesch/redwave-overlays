from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from backend.routers import apis
from backend.routers.views import main_views, overlay_detail_views, overlay_window_views

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.mount("/static", StaticFiles(directory="frontend/static"), name="static")

# Подключаем маршруты
app.include_router(main_views.router)
app.include_router(overlay_detail_views.router, prefix="/overlays")
app.include_router(overlay_window_views.router)
app.include_router(apis.router)
