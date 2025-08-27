import json
import pytest

from backend.database import data_loader


@pytest.fixture
def fake_cards_file(tmp_path):
    file = tmp_path / "cards.json"
    cards = [{"title": "Card1", "value": 10}, {"title": "Card2", "value": 20}]
    json.dump(cards, open(file, "w", encoding="utf-8"))
    data_loader.DB_PATH = file

    data_loader._load_cards.cache_clear()
    return cards


@pytest.fixture
def fake_metadata_file(tmp_path):
    file = tmp_path / "metadata.json"
    metadata = {"app_version": "1.0.0", "overlays": {"overlay1": "v1"}}
    json.dump(metadata, open(file, "w", encoding="utf-8"))
    data_loader.METADATA_PATH = file

    data_loader._load_metadata.cache_clear()
    return metadata


@pytest.fixture
def bad_json_file(tmp_path):
    def _factory(name):
        file = tmp_path / name
        file.write_text("{ bad json }", encoding="utf-8")
        return file

    return _factory


# --- Data tests ---


def test_load_cards_data(fake_cards_file):
    cards = data_loader.load_cards_data()
    assert len(cards) == 2
    assert cards[0]["title"] == "Card1"


def test_get_card_data_by_title(fake_cards_file):
    card = data_loader.get_card_data_by_title("Card1")
    assert card["value"] == 10
    assert data_loader.get_card_data_by_title("NoCard") is None


def test_get_app_version(fake_metadata_file):
    assert data_loader.get_app_version() == "1.0.0"


def test_get_overlay_version(fake_metadata_file):
    assert data_loader.get_overlay_version("overlay1") == "v1"
    assert data_loader.get_overlay_version("overlay2") is None


# --- Error tests ---


def test_load_cards_file_not_found(tmp_path):
    data_loader.DB_PATH = tmp_path / "missing.json"
    data_loader._load_cards.cache_clear()
    cards = data_loader.load_cards_data()
    assert cards == []


def test_load_metadata_file_not_found(tmp_path):
    data_loader.METADATA_PATH = tmp_path / "missing.json"
    data_loader._load_metadata.cache_clear()
    metadata = data_loader._load_metadata()
    assert metadata == {}


def test_load_cards_json_decode_error(bad_json_file):
    data_loader.DB_PATH = bad_json_file("bad_cards.json")
    data_loader._load_cards.cache_clear()
    cards = data_loader.load_cards_data()
    assert cards == []


def test_load_metadata_json_decode_error(bad_json_file):
    data_loader.METADATA_PATH = bad_json_file("bad_metadata.json")
    data_loader._load_metadata.cache_clear()
    metadata = data_loader._load_metadata()
    assert metadata == {}
