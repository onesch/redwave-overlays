import json
from pathlib import Path
from typing import Optional, Dict, Any
from functools import lru_cache

from backend.utils.paths import get_base_path

BASE_PATH = get_base_path()

DB_PATH = BASE_PATH / "backend" / "database" / "card_desc_database.json"
METADATA_PATH = BASE_PATH / "backend" / "database" / "metadata.json"


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
            data = json.load(f)
            return data
    except FileNotFoundError:
        print(f"Metadata file not found at {METADATA_PATH}.")
        return {}
    except json.JSONDecodeError:
        print(f"Metadata file at {METADATA_PATH} is invalid JSON.")
        return {}


def get_app_version() -> Optional[str]:
    return _load_metadata().get("app_version")
