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


@pytest.fixture
def fake_changelog_img_path(tmp_path):
    path = tmp_path / "changelog_versions"
    path.mkdir()

    data_loader.CHANGELOG_IMG_PATH = path
    return path


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


def test_get_overlays_card_data_with_selection(fake_cards_file):
    overlays, selected_info, card_data = data_loader.get_overlays_card_data("card2")
    
    assert len(overlays) == 2
    assert overlays[0]["key"] == "card1"
    assert overlays[1]["key"] == "card2"

    assert selected_info["key"] == "card2"
    assert selected_info["template"] == "pages/card_detail/card2.html"

    assert card_data["title"] == "Card2"
    assert card_data["value"] == 20


def test_get_changelog_images_success(fake_changelog_img_path):
    (fake_changelog_img_path / "v0.0.0.png").write_text("", encoding="utf-8")
    (fake_changelog_img_path / "v0.0.1.png").write_text("", encoding="utf-8")

    images = data_loader.get_changelog_images()

    assert images == [
        "images/changelog_versions/v0.0.0.png",
        "images/changelog_versions/v0.0.1.png",
    ]


# --- Error/Negative tests ---


def test_get_overlays_card_data_no_selection(fake_cards_file):
    overlays, selected_info, card_data = data_loader.get_overlays_card_data(None)
    
    assert selected_info["key"] == "card1"
    assert selected_info["template"] == "pages/card_detail/card1.html"

    assert card_data["title"] == "Card1"
    assert card_data["value"] == 10


def test_get_overlays_card_data_empty_list(tmp_path):
    file = tmp_path / "cards.json"
    file.write_text("[]", encoding="utf-8")
    data_loader.DB_PATH = file
    data_loader._load_cards.cache_clear()

    overlays, selected_info, card_data = data_loader.get_overlays_card_data(None)
    assert overlays == []
    assert selected_info is None
    assert card_data is None


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


def test_get_changelog_images_dir_not_exists(tmp_path, monkeypatch):
    non_exist_dir = tmp_path / "changelog_versions"
    monkeypatch.setattr(data_loader, "CHANGELOG_IMG_PATH", non_exist_dir)

    images = data_loader.get_changelog_images()
    assert images == []


def test_get_changelog_images_empty_dir(fake_changelog_img_path):
    images = data_loader.get_changelog_images()
    assert images == []


def test_get_changelog_images_ignore_non_png(fake_changelog_img_path):
    (fake_changelog_img_path / "readme.txt").write_text("test")
    (fake_changelog_img_path / "data.jpg").write_text("test")

    images = data_loader.get_changelog_images()
    assert images == []
