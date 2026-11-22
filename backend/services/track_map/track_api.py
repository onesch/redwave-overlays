import logging
import httpx
from typing import Any, Literal
from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    ValidationError,
)

TRACK_API_URL = (
    "https://redwave-overlays-trackmap-api.redwave-overlays.workers.dev"
    "/tracks/{track_id}"
)
REQUEST_TIMEOUT_S = 5.0

logger = logging.getLogger(__name__)


class StartFinish(BaseModel):
    """
    Start/finish line location and the direction of travel.

    pct: lap fraction (0-1) along the points where the line is drawn.
    direction: 1 if cars move in the order of the points, -1 otherwise.
    """

    model_config = ConfigDict(allow_inf_nan=False)

    pct: float = Field(ge=0, le=1)
    direction: Literal[1, -1]


class TrackGeometry(BaseModel):
    """
    Track geometry as returned by the Track Map API.

    The points form the track's closed loop. The API also sends a viewBox,
    which is ignored: the overlay fits the view box to the points itself.
    """

    model_config = ConfigDict(allow_inf_nan=False)

    points: list[tuple[float, float]] = Field(min_length=2)
    start_finish: StartFinish


def fetch_track_geometry(track_id: int) -> dict[str, Any] | None:
    """
    Fetch and validate the track geometry.

    :param track_id: iRacing track ID (WeekendInfo.TrackID)
    :return: {"points", "start_finish"} ready for the
             overlay DTO, or None if the track is unavailable
             or the response is malformed.
    """
    url = TRACK_API_URL.format(track_id=track_id)
    try:
        response = httpx.get(url, timeout=REQUEST_TIMEOUT_S)
        response.raise_for_status()
        geometry = TrackGeometry.model_validate(response.json())
    except httpx.HTTPStatusError as e:
        retry_after = None
        try:
            error_data = e.response.json()
            retry_after = error_data.get("retry_after")
        except ValueError:
            pass
        logger.warning(
            "Track %s map unavailable: HTTP %s, retry_after=%s",
            track_id,
            e.response.status_code,
            retry_after,
        )
        return None
    except httpx.HTTPError as e:
        logger.warning("Track %s map request failed: %s", track_id, e)
        return None
    except (ValueError, ValidationError) as e:
        # ValueError covers a body that is not JSON.
        logger.warning("Track %s map response is malformed: %s", track_id, e)
        return None

    return geometry.model_dump()
