from fastapi.templating import Jinja2Templates
from backend.utils.paths import get_base_path

BASE_PATH = get_base_path()
templates = Jinja2Templates(directory=BASE_PATH / "frontend" / "templates")
