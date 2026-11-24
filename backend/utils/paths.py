import os
import sys
from pathlib import Path

# Electron's app name (package.json "productName"): the folder name
# of app.getPath("userData").
APP_DIR_NAME = "RedWave overlays"
# Set by the Electron app when it starts the backend executable.
USER_DATA_DIR_ENV = "REDWAVE_USER_DATA_DIR"


def get_base_path() -> Path:
    """
    Return the root directory of the bundled app resources.

    In a PyInstaller build this is the temporary extraction directory
    (sys._MEIPASS); in development it is the project root.
    """
    if getattr(sys, "frozen", False):
        return Path(sys._MEIPASS)
    return Path(__file__).resolve().parents[2]


def get_user_data_path() -> Path:
    """
    Return the writable directory for persistent user data.

    This is Electron's userData folder (also used for the app settings).
    Electron passes it to the backend in `REDWAVE_USER_DATA_DIR`; when the
    backend is started directly (e.g. uvicorn in dev), it is resolved
    from %APPDATA% the same way Electron does.
    """
    env_path = os.environ.get(USER_DATA_DIR_ENV)
    if env_path:
        return Path(env_path)

    # %APPDATA% is the base of Electron's userData.
    appdata = os.environ.get("APPDATA") or Path.home() / "AppData" / "Roaming"
    return Path(appdata) / APP_DIR_NAME
