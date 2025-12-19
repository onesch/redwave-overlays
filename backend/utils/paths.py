import sys
from pathlib import Path


def get_base_path() -> Path:
    """
    Base path for app resources.
    Works for:
    - dev (python / uvicorn)
    - PyInstaller onefile
    """
    if getattr(sys, "frozen", False):
        return Path(sys._MEIPASS)
    return Path(__file__).resolve().parents[2]
