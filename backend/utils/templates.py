from fastapi.templating import Jinja2Templates

from backend.utils.paths import get_base_path
from backend.database.data_loader import get_app_version

BASE_PATH = get_base_path()

def app_context(request):
    return {
        "app_version": get_app_version(),
    }

templates = Jinja2Templates(
    directory=BASE_PATH / "frontend" / "templates",
    context_processors=[app_context],
)
