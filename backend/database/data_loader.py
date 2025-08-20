import json
from pathlib import Path
from typing import Optional, Dict, Any

DB_PATH = Path("backend/database/card_desc_database.json")
METADATA_PATH = Path("backend/database/metadata.json")

_cards_data = None
_cards_index = None
_metadata_cache: Optional[Dict[str, Any]] = None


def _load_cards():
    global _cards_data, _cards_index
    with DB_PATH.open("r", encoding="utf-8") as f:
        _cards_data = json.load(f)
        _cards_index = {card.get("title"): card for card in _cards_data}


def load_cards_data():
    global _cards_data
    if _cards_data is None:
        _load_cards()
    return _cards_data


def get_card_data_by_title(title: str) -> Optional[dict]:
    global _cards_index
    if _cards_index is None:
        _load_cards()
    return _cards_index.get(title)


def _load_metadata() -> Dict[str, Any]:
    global _metadata_cache
    if _metadata_cache is None:
        with METADATA_PATH.open("r", encoding="utf-8") as f:
            _metadata_cache = json.load(f)
    return _metadata_cache


def get_app_version() -> Optional[str]:
    data = _load_metadata()
    return data.get("app_version")


def get_overlay_version(name: str) -> Optional[str]:
    data = _load_metadata()
    overlays = data.get("overlays", {})
    return overlays.get(name)
