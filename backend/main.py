from fastapi import FastAPI
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


@app.get("/api/irsdk", response_model=IRSDKSchemas)
def get_irsdk_data():
    speed_ms = irsdk_service.get_value("Speed")
    throttle = irsdk_service.get_value("Throttle")
    brake = irsdk_service.get_value("Brake")
    speed_kmh = round(speed_ms * 3.6, 1) if speed_ms is not None else None
    return IRSDKSchemas(
        speed=speed_kmh,
        throttle=throttle,
        brake=brake,
    )
