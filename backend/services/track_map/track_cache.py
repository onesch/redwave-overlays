import json
import logging
import os
import threading
from pathlib import Path
from typing import Any

from backend.services.track_map.track_api import TrackGeometry

TRACK_CACHE_FILENAME = "track_geometry_cache.json"

logger = logging.getLogger(__name__)


def _validate_entry(entry: Any) -> dict[str, Any]:
    """
    Validates a cached entry (the dict fetch_track_geometry returns)
    and normalizes it to the same form.
    """
    if not isinstance(entry, dict):
        raise TypeError(f"expected an object, got {type(entry).__name__}")
    # TrackGeometry reads the view box from its API alias.
    data = {**entry, "viewBox": entry.get("view_box")}
    return TrackGeometry.model_validate(data).model_dump()


class TrackGeometryCache:
    """
    Persistent track geometry cache: {track_id: geometry}.

    The JSON file is read once on creation; every successful put()
    updates the in-memory dict and rewrites the file.
    """

    def __init__(self, path: Path):
        self.path = path
        self._lock = threading.Lock()
        self._tracks: dict[int, dict[str, Any]] = self._load()

    def get(self, track_id: int) -> dict[str, Any] | None:
        """Returns the cached geometry, or None on a miss."""
        return self._tracks.get(track_id)

    def put(self, track_id: int, geometry: dict[str, Any]) -> None:
        """Stores the geometry in memory and saves the cache file."""
        with self._lock:
            self._tracks[track_id] = geometry
            self._save()

    def _load(self) -> dict[int, dict[str, Any]]:
        """
        Reads the cache file. A missing, unreadable or malformed file
        gives an empty cache; invalid entries are skipped.
        """
        try:
            with self.path.open("r", encoding="utf-8") as f:
                raw = json.load(f)
        except FileNotFoundError:
            return {}
        except (OSError, ValueError) as e:
            # ValueError covers invalid JSON and invalid UTF-8.
            logger.warning("Track cache %s is unreadable: %s", self.path, e)
            return {}

        if not isinstance(raw, dict):
            logger.warning("Track cache %s is not an object", self.path)
            return {}

        tracks: dict[int, dict[str, Any]] = {}
        for key, entry in raw.items():
            try:
                tracks[int(key)] = _validate_entry(entry)
            except (TypeError, ValueError) as e:
                # ValueError covers pydantic's ValidationError.
                logger.warning("Track cache entry %r skipped: %s", key, e)
        return tracks

    def _save(self) -> None:
        """
        Writes the cache through a temporary file, so an interrupted
        write never leaves a truncated cache behind.
        """
        tmp_path = self.path.with_name(self.path.name + ".tmp")
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with tmp_path.open("w", encoding="utf-8") as f:
                json.dump(self._tracks, f)
            os.replace(tmp_path, self.path)
        except (OSError, TypeError, ValueError) as e:
            logger.warning("Track cache %s not saved: %s", self.path, e)
