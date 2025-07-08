from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware

from backend.services.irsdk_service.schemas import IRSDKSchemas
from backend.services.irsdk_service.service import IRSDKService


app = FastAPI()
irsdk_service = IRSDKService()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.mount("/static", StaticFiles(directory="frontend/static"), name="static")
templates = Jinja2Templates(directory="frontend/templates")


# HTML
@app.get("/main_window", response_class=HTMLResponse)
async def main_window_view(request: Request):
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request
        }
    )


@app.get("/speed", response_class=HTMLResponse)
async def speed_page(request: Request):
    return templates.TemplateResponse("speed.html", {"request": request})


@app.get("/controls", response_class=HTMLResponse)
async def controls_page(request: Request):
    return templates.TemplateResponse("controls.html", {"request": request})


# API (для JavaScript)
@app.get("/api/speed", response_model=IRSDKSchemas)
def get_speed_data():
    speed = irsdk_service.get_speed("kmh")

    return IRSDKSchemas(
        speed=speed,
    )

@app.get("/api/controls", response_model=IRSDKSchemas)
def get_controls_data():
    throttle  = irsdk_service.get_throttle()
    brake  = irsdk_service.get_brake()

    return IRSDKSchemas(
        throttle=throttle,
        brake=brake,
    )
