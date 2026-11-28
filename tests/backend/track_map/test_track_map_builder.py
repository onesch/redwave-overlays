import pytest

from backend.services.track_map.service import TrackMapCarBuilder


# --- Positive tests ---


def test_track_map_builder_adds_class_data(mock_builder, mock_ctx):
    ctx = mock_ctx()
    car = mock_builder.build(0, ctx)

    assert car["car_idx"] == 0
    assert car["car_number"] == "12"
    assert car["lap_dist_pct"] == pytest.approx(0.3)
    assert car["is_in_pitroad"] is False
    assert car["class_id"] == 1
    assert car["color"] == "#ff0000"


@pytest.mark.parametrize(
    "delta,expected",
    [
        (1, (True, False)),
        (-2, (False, True)),
        (0, (False, False)),
        (None, (False, False)),
    ],
)
def test_track_map_builder_adds_lap_flags_from_context(
    mock_builder,
    mock_ctx,
    delta,
    expected,
):
    deltas = {} if delta is None else {1: delta}
    ctx = mock_ctx(lap_deltas=deltas)

    car = mock_builder.build(1, ctx)

    assert (car["is_lap_ahead"], car["is_lap_behind"]) == expected


# --- Negative tests ---


def test_track_map_builder_returns_none_when_base_build_none(
        mock_builder,
        mock_ctx,
        monkeypatch
):
    ctx = mock_ctx()

    monkeypatch.setattr(
        TrackMapCarBuilder,
        "build",
        lambda self, idx, ctx: None
    )

    car = mock_builder.build(0, ctx)
    assert car is None
