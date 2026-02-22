import json
from typing import Optional, Dict, Any
from functools import lru_cache

from backend.utils.paths import get_base_path

BASE_PATH = get_base_path()

DB_PATH = BASE_PATH / "backend" / "database" / "card_desc_database.json"
METADATA_PATH = BASE_PATH / "backend" / "database" / "metadata.json"
CHANGELOG_IMG_PATH = (
    BASE_PATH / "frontend" / "static" / "images" / "changelog_versions"
)


@lru_cache(maxsize=1)
def _load_cards() -> tuple[list[dict], Dict[str, dict]]:
    """
    Load cards from JSON file and create
    an index by key for safe frontend usage.
    """
    try:
        with DB_PATH.open("r", encoding="utf-8") as f:
            cards_data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        cards_data = []

    cards_index = {card["key"]: card for card in cards_data}
    return cards_data, cards_index


def load_cards_data() -> list[dict]:
    """Return list of all cards."""
    return _load_cards()[0]


def get_card_data_by_key(key: str) -> Optional[dict]:
    """Get card by key (safe for URLs/templates)."""
    return _load_cards()[1].get(key)


@lru_cache(maxsize=1)
def _load_metadata() -> Dict[str, Any]:
    """Load application metadata from JSON file."""
    try:
        with METADATA_PATH.open("r", encoding="utf-8") as f:
            data = json.load(f)
            return data
    except (FileNotFoundError, json.JSONDecodeError):
        print(f"Invalid {METADATA_PATH}.")
        return {}


def get_app_version() -> Optional[str]:
    return _load_metadata().get("app_version")


def get_overlays_card_data(
    selected_key: str | None = None,
) -> tuple[list[dict], dict, dict]:
    """
    Returns overlays list, selected overlay info, and card data.
    Automatically selects first overlay if selected_overlay is None.
    """
    cards = load_cards_data()
    if not cards:
        return [], None, None

    overlays = [
        {
            "key": card["key"],
            "title": card["title"],
            "icon": card.get("icon"),
        }
        for card in cards
    ]

    if not selected_key:
        selected_key = overlays[0]["key"]

    card_data = get_card_data_by_key(selected_key)
    selected_overlay_info = {
        "key": selected_key,
        "template": f"pages/card_detail/{selected_key}.html",
    }

    return overlays, selected_overlay_info, card_data


def get_changelog_images() -> list[str]:
    """
    Return a sorted list of changelog image paths.
    """
    if not CHANGELOG_IMG_PATH.exists():
        return []

    images = [
        f"images/changelog_versions/{file.name}"
        for file in CHANGELOG_IMG_PATH.glob("*.png")
    ]
    images.sort(reverse=True)
    return images
