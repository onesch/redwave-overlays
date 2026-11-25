import pytest

from backend.components.lap_relation import LapRelations
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
        (1, "ahead_lap"),
        (-2, "behind_lap"),
        (0, None),
        (None, None),
    ],
)
def test_track_map_builder_adds_lap_diff_from_context(
    mock_builder,
    mock_ctx,
    delta,
    expected,
):
    deltas = {} if delta is None else {1: delta}
    ctx = mock_ctx(lap_relations=LapRelations(deltas))

    car = mock_builder.build(1, ctx)

    assert car["lap_diff"] == expected


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
