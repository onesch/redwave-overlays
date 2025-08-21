import json
from pathlib import Path
from typing import Optional, Dict, Any
from functools import lru_cache

DB_PATH = Path("backend/database/card_desc_database.json")
METADATA_PATH = Path("backend/database/metadata.json")


@lru_cache(maxsize=1)
def _load_cards() -> tuple[list[dict], Dict[str, dict]]:
    """Loading card and creating index by title"""
    try:
        with DB_PATH.open("r", encoding="utf-8") as f:
            cards_data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        cards_data = []
    cards_index = {card.get("title"): card for card in cards_data}
    return cards_data, cards_index


def load_cards_data() -> list[dict]:
    return _load_cards()[0]


def get_card_data_by_title(title: str) -> Optional[dict]:
    return _load_cards()[1].get(title)


@lru_cache(maxsize=1)
def _load_metadata() -> Dict[str, Any]:
    """Load application metadata from JSON file."""
    try:
        with METADATA_PATH.open("r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def get_app_version() -> Optional[str]:
    return _load_metadata().get("app_version")


def get_overlay_version(name: str) -> Optional[str]:
    return _load_metadata().get("overlays", {}).get(name)
