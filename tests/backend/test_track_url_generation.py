from types import SimpleNamespace
import pytest

from backend.utils import track_url_generation


# --- Data tests ---


@pytest.mark.parametrize(
    "track_id,track_name,shortname,expected_part",
    [
        (
            191,
            "Daytona International Speedway",
            "daytona",
            "tracks_daytona_2011/191-daytona-international-speedway/active.svg",
        ),
        (
            5000,
            "Mount Panorama Circuit",
            "bathurst",
            "tracks_bathurst/5000-mount-panorama-circuit/active.svg",
        ),
    ],
)
def test_make_track_svg_url_uses_expected_shortname(
    track_id, track_name, shortname, expected_part
):
    url = track_url_generation.make_track_svg_url(
        track_id=track_id,
        track_name=track_name,
        shortname=shortname,
    )
    assert url.startswith(
        "https://members-assets.iracing.com/public/track-maps/"
    )
    assert expected_part in url


def test_make_track_svg_url_uses_custom_svg_type():
    url = track_url_generation.make_track_svg_url(
        track_id=5000,
        track_name="Mount Panorama Circuit",
        shortname="bathurst",
        svg_type="start-finish",
    )
    assert url.endswith("/start-finish.svg")


def test_extract_first_subpath_returns_svg_with_first_path_only():
    svg = (
        '<svg xmlns="http://www.w3.org/2000/svg">'
        '<path d="M0 0 L10 10 Z M20 20 L30 30 Z"/>'
        "</svg>"
    )

    result = track_url_generation.extract_first_subpath(svg)

    assert 'd="M0 0 L10 10 Z"' in result
    assert "M20 20 L30 30 Z" not in result


def test_extract_first_subpath_returns_original_when_path_missing():
    svg = "<svg><g></g></svg>"
    result = track_url_generation.extract_first_subpath(svg)
    assert result == svg


def test_fetch_svg_success_without_extract(monkeypatch):
    called = {"extract": 0}

    def fake_extract(text):
        called["extract"] += 1
        return "<svg>processed</svg>"

    def fake_get(url, timeout):
        return SimpleNamespace(status_code=200, text="<svg>raw</svg>")

    monkeypatch.setattr(
        track_url_generation, "extract_first_subpath", fake_extract
    )
    monkeypatch.setattr(track_url_generation.httpx, "get", fake_get)

    result = track_url_generation.fetch_svg(
        "http://test/svg", extract_first=False
    )

    assert result == "<svg>raw</svg>"
    assert called["extract"] == 0


def test_fetch_svg_success_with_extract(monkeypatch):
    def fake_extract(text):
        assert text == "<svg>raw</svg>"
        return "<svg>processed</svg>"

    def fake_get(url, timeout):
        return SimpleNamespace(status_code=200, text="<svg>raw</svg>")

    monkeypatch.setattr(
        track_url_generation, "extract_first_subpath", fake_extract
    )
    monkeypatch.setattr(track_url_generation.httpx, "get", fake_get)

    result = track_url_generation.fetch_svg(
        "http://test/svg", extract_first=True
    )
    assert result == "<svg>processed</svg>"


# --- Error tests ---


def test_extract_first_subpath_returns_original_when_svg_invalid():
    invalid_svg = "<svg><path d='M0 0'"
    result = track_url_generation.extract_first_subpath(invalid_svg)
    assert result == invalid_svg


def test_fetch_svg_returns_none_when_status_is_not_200(monkeypatch):
    def fake_get(url, timeout):
        return SimpleNamespace(status_code=404, text="")

    monkeypatch.setattr(track_url_generation.httpx, "get", fake_get)

    result = track_url_generation.fetch_svg(
        "http://test/svg", extract_first=True
    )
    assert result is None


def test_fetch_svg_returns_none_when_http_client_raises(monkeypatch):
    def fake_get(url, timeout):
        raise RuntimeError("network error")

    monkeypatch.setattr(track_url_generation.httpx, "get", fake_get)

    result = track_url_generation.fetch_svg("http://test/svg")
    assert result is None
