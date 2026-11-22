import gzip
import json

import pytest

from backend.services.track_map.track_cache import TrackGeometryCache

GEOMETRY = {
    "points": [(0.0, 0.0), (10.0, 0.0), (0.0, 0.0)],
    "start_finish": {"pct": 0.5, "direction": 1},
}


def _write_cache(path, data) -> None:
    """Writes a cache file the same way TrackGeometryCache does."""
    with gzip.open(path, "wt", encoding="utf-8") as f:
        json.dump(data, f)


# --- Positive tests ---


def test_missing_file_gives_empty_cache(tmp_path):
    cache = TrackGeometryCache(tmp_path / "cache.json.gz")

    assert cache.get(1) is None


def test_put_is_persisted_between_instances(tmp_path):
    path = tmp_path / "cache.json.gz"

    TrackGeometryCache(path).put(145, GEOMETRY)
    geometry = TrackGeometryCache(path).get(145)

    assert geometry == GEOMETRY


def test_get_serves_from_memory_without_reading_disk(tmp_path):
    path = tmp_path / "cache.json.gz"
    _write_cache(path, {"145": GEOMETRY})
    cache = TrackGeometryCache(path)

    # The file is read once on creation; later changes on disk are unseen.
    path.unlink()

    assert cache.get(145) == GEOMETRY


def test_put_writes_gzip_file_without_temp_leftovers(tmp_path):
    path = tmp_path / "nested" / "cache.json.gz"

    TrackGeometryCache(path).put(145, GEOMETRY)

    assert path.read_bytes()[:2] == b"\x1f\x8b"  # gzip signature
    assert list(path.parent.iterdir()) == [path]


# --- Negative tests ---


@pytest.mark.parametrize(
    "content",
    [
        b'{"145": {}}',  # plain JSON, not gzip
        gzip.compress(b'{"145": {}}')[:10],  # truncated archive
        gzip.compress(b"not json"),
        gzip.compress(b"[]"),  # not an object
    ],
)
def test_unreadable_file_gives_empty_cache(tmp_path, content):
    path = tmp_path / "cache.json.gz"
    path.write_bytes(content)

    assert TrackGeometryCache(path).get(145) is None


def test_invalid_entries_are_skipped(tmp_path):
    path = tmp_path / "cache.json.gz"
    _write_cache(
        path,
        {
            "145": GEOMETRY,
            "214": {"points": [[0, 0]]},  # too few points, no start_finish
            "not-an-id": GEOMETRY,
            "300": "geometry",
        },
    )

    cache = TrackGeometryCache(path)

    assert cache.get(145) == GEOMETRY
    assert cache.get(214) is None
    assert cache.get(300) is None


def test_failed_save_keeps_geometry_in_memory(tmp_path):
    # A directory in place of the cache file makes every save fail.
    path = tmp_path / "cache.json.gz"
    path.mkdir()
    cache = TrackGeometryCache(path)

    cache.put(145, GEOMETRY)

    assert cache.get(145) == GEOMETRY
