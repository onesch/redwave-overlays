# --- Positive tests ---


def test_build_returns_car_data(mock_builder, mock_ctx):
    ctx = mock_ctx()

    car = mock_builder.build(0, ctx)

    assert car == {
        "car_idx": 0,
        "car_number": "12",
        "lap_dist_pct": 0.3,
        "is_in_pitroad": False,
    }


def test_is_pace_car_case_insensitive(mock_builder):
    driver = {"UserName": "pace car"}

    assert mock_builder._is_pace_car(driver) is True


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


def test_is_pace_car_returns_false_for_normal_driver(mock_builder):
    driver = {"UserName": "Driver1"}

    assert mock_builder._is_pace_car(driver) is False
