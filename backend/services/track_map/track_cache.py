import gzip
import json
import logging
import os
import threading
import zlib
from pathlib import Path
from typing import Any

from backend.services.track_map.track_api import TrackGeometry

# Stored as compressed JSON.
TRACK_CACHE_FILENAME = "track_geometry_cache.json.gz"

logger = logging.getLogger(__name__)


def _validate_entry(entry: Any) -> dict[str, Any]:
    """
    Validate a cached entry and normalize it.

    The entry has the same shape as the result of fetch_track_geometry,
    and is checked by the same TrackGeometry model as an API response.

    :raises TypeError: if the entry is not an object.
    :raises ValueError: if the entry fails validation (pydantic's
        ValidationError is a ValueError).
    """
    if not isinstance(entry, dict):
        raise TypeError(f"expected an object, got {type(entry).__name__}")

    return TrackGeometry.model_validate(entry).model_dump()


class TrackGeometryCache:
    """
    Persistent cache of track geometries, keyed by track id.

    The file is read once on creation and served from memory afterwards.
    Every put() updates the memory and rewrites the file, so geometry
    survives app restarts without repeated API requests.
    """

    def __init__(self, path: Path):
        """
        :param path: location of the cache file; it does not have to exist.
        """
        self.path = path
        self._lock = threading.Lock()
        self._tracks: dict[int, dict[str, Any]] = self._load()

    def get(self, track_id: int) -> dict[str, Any] | None:
        """
        Return the cached geometry of a track.

        :param track_id: iRacing track ID.
        :return: the geometry, or None if the track is not cached.
        """
        return self._tracks.get(track_id)

    def put(self, track_id: int, geometry: dict[str, Any]) -> None:
        """
        Cache the geometry of a track in memory and save the cache file.

        :param track_id: iRacing track ID.
        :param geometry: validated geometry from fetch_track_geometry.
        """
        # Serialize writers so two saves never overwrite each other.
        with self._lock:
            self._tracks[track_id] = geometry
            self._save()

    def _load(self) -> dict[int, dict[str, Any]]:
        """
        Read and validate the cache file.

        A missing, unreadable or malformed file gives an empty cache,
        and invalid entries are skipped, so a damaged cache never breaks
        the app: the geometry is just fetched from the API again.
        """
        # Read the whole file; a missing file is a normal first run.
        try:
            with gzip.open(self.path, "rt", encoding="utf-8") as f:
                raw = json.load(f)
        except FileNotFoundError:
            return {}
        except (OSError, EOFError, zlib.error, ValueError) as e:
            # Not an archive (OSError), truncated or corrupted archive
            # (EOFError, zlib.error), invalid JSON or UTF-8 (ValueError).
            logger.warning("Track cache %s is unreadable: %s", self.path, e)
            return {}

        if not isinstance(raw, dict):
            logger.warning("Track cache %s is not an object", self.path)
            return {}

        # Keep only entries that pass the same validation as API data.
        tracks: dict[int, dict[str, Any]] = {}
        for key, entry in raw.items():
            try:
                # JSON object keys are strings, track ids are integers.
                tracks[int(key)] = _validate_entry(entry)
            except (TypeError, ValueError) as e:
                logger.warning("Track cache entry %r skipped: %s", key, e)
        return tracks

    def _save(self) -> None:
        """
        Write the whole cache to disk atomically.

        The data goes to a temporary file that then replaces the cache
        file, so an interrupted write never leaves a truncated cache.
        A failed save is only logged: the in-memory cache keeps working.
        """
        tmp_path = self.path.with_name(self.path.name + ".tmp")
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)

            # Compact JSON, compressed on the fly.
            with gzip.open(tmp_path, "wt", encoding="utf-8") as f:
                json.dump(self._tracks, f, separators=(",", ":"))

            # Atomic on the same volume: readers see the old or new file.
            os.replace(tmp_path, self.path)
        except (OSError, TypeError, ValueError) as e:
            logger.warning("Track cache %s not saved: %s", self.path, e)
