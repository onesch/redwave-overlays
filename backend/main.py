import sys
import os
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from backend.utils.paths import get_base_path
from backend.routers import apis
from backend.routers.views import (
    main_views,
    overlay_window_views,
)

app = FastAPI()
BASE_PATH = get_base_path()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount(
    "/static",
    StaticFiles(directory=BASE_PATH / "frontend" / "static"),
    name="static",
)

app.include_router(main_views.router)
app.include_router(overlay_window_views.router)
app.include_router(apis.router)

if __name__ == "__main__":
    import uvicorn

    sys.stdin = open(os.devnull)

    try:
        uvicorn.run(
            app,
            host="127.0.0.1",
            port=8000,
            log_level="info"
        )
    except Exception as e:
        logging.error("Uvicorn failed: %s", e)
