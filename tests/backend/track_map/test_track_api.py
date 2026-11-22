import httpx
import pytest

from backend.services.track_map import track_api


def _payload(**overrides) -> dict:
    payload = {
        "viewBox": "0 0 1920 1080",
        "points": [[1740.7, 469.7], [1740.656, 467.338], [1740.7, 469.7]],
        "start_finish": {"pct": 0.74533658, "direction": 1},
    }
    payload.update(overrides)
    return payload


@pytest.fixture
def fake_get(monkeypatch):
    """
    Replaces httpx.get; `respond(status, json=..., content=...)` sets
    the response and `requests` records the requested URLs.
    """
    state = {"response": None, "requests": []}

    def _get(url, timeout):
        state["requests"].append(url)
        response = state["response"]
        if isinstance(response, Exception):
            raise response
        return response

    def respond(status_code=200, **kwargs):
        state["response"] = httpx.Response(
            status_code,
            request=httpx.Request("GET", "https://test"),
            **kwargs,
        )

    monkeypatch.setattr(track_api.httpx, "get", _get)
    state["respond"] = respond
    return state


# --- Positive tests ---


def test_fetch_track_geometry_requests_track_by_id(fake_get):
    fake_get["respond"](json=_payload())

    track_api.fetch_track_geometry(145)

    assert fake_get["requests"] == [
        "https://redwave-overlays-trackmap-api.redwave-overlays.workers.dev"
        "/tracks/145"
    ]


def test_fetch_track_geometry_returns_normalized_geometry(fake_get):
    fake_get["respond"](json=_payload())

    geometry = track_api.fetch_track_geometry(145)

    assert geometry == {
        "points": [
            (1740.7, 469.7),
            (1740.656, 467.338),
            (1740.7, 469.7),
        ],
        "start_finish": {"pct": 0.74533658, "direction": 1},
    }


def test_fetch_track_geometry_accepts_reverse_direction(fake_get):
    fake_get["respond"](
        json=_payload(start_finish={"pct": 0, "direction": -1})
    )

    geometry = track_api.fetch_track_geometry(214)

    assert geometry["start_finish"] == {"pct": 0.0, "direction": -1}


# --- Error tests ---


@pytest.mark.parametrize("status_code", [400, 404, 429, 500])
def test_fetch_track_geometry_returns_none_on_http_error(
    fake_get, status_code
):
    fake_get["respond"](status_code, json={"error": "Track not found"})

    assert track_api.fetch_track_geometry(1) is None


def test_fetch_track_geometry_returns_none_on_network_error(fake_get):
    fake_get["response"] = httpx.ConnectTimeout("timeout")

    assert track_api.fetch_track_geometry(145) is None


def test_fetch_track_geometry_returns_none_on_non_json_body(fake_get):
    fake_get["respond"](content=b"<html>oops</html>")

    assert track_api.fetch_track_geometry(145) is None


@pytest.mark.parametrize(
    "payload",
    [
        [],
        {"error": "Track not found"},
        _payload(points=[[1, 2]]),
        _payload(points=[[1, 2], [3]]),
        _payload(points=[[1, 2], [3, None]]),
        _payload(start_finish={"pct": 1.5, "direction": 1}),
        _payload(start_finish={"pct": 0.5, "direction": 0}),
        _payload(start_finish={"pct": 0.5}),
        {"viewBox": "0 0 1920 1080", "points": [[0, 0], [1, 1]]},
    ],
)
def test_fetch_track_geometry_returns_none_on_malformed_payload(
    fake_get, payload
):
    fake_get["respond"](json=payload)

    assert track_api.fetch_track_geometry(145) is None


def test_fetch_track_geometry_rejects_non_finite_numbers(fake_get):
    # Python's JSON parser accepts NaN/Infinity literals.
    fake_get["respond"](
        content=(
            b'{"viewBox": "0 0 1920 1080", "points": [[0, NaN], [1, 1]],'
            b' "start_finish": {"pct": 0.5, "direction": 1}}'
        )
    )

    assert track_api.fetch_track_geometry(145) is None
