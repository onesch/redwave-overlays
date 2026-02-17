from backend.services.track_map.service import TrackMapCarBuilder


# --- Positive tests ---


def test_track_map_builder_adds_class_color(mock_builder, mock_ctx):
    ctx = mock_ctx()
    car = mock_builder.build(0, ctx)

    assert car == {
        "car_idx": 0,
        "car_number": "12",
        "lap_dist_pct": 0.3,
        "is_in_pitroad": False,
        "car_class_color": 16711680,
    }


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
