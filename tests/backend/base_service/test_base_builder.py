import pytest


# --- Positive tests ---


def test_build_returns_car_data(mock_builder, mock_ctx):
    ctx = mock_ctx()

    car = mock_builder.build(0, ctx)

    assert car["car_idx"] == 0
    assert car["car_number"] == "12"
    assert car["lap_dist_pct"] == pytest.approx(0.3)
    assert car["is_in_pitroad"] is False


def test_build_returns_none_for_pace_car_flag(mock_builder, mock_ctx):
    ctx = mock_ctx(
        drivers=[{"UserName": "Safety", "CarNumber": "0", "CarIsPaceCar": 1}],
        lap_dist_pct=[0.0],
        is_pitroad=[False],
        positions=[0],
        class_positions=[0],
    )

    assert mock_builder.build(0, ctx) is None


# --- Negative tests ---


def test_build_returns_none_for_pace_car(mock_builder, mock_ctx):
    ctx = mock_ctx(
        drivers=[
            {"UserName": "PACE CAR", "CarNumber": "0"},
        ],
        lap_dist_pct=[0.0],
        is_pitroad=[False],
        positions=[0],
        class_positions=[0],
    )

    result = mock_builder.build(0, ctx)

    assert result is None

