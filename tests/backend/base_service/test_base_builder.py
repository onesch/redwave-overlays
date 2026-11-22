import pytest

from backend.services.base import is_multiclass, is_pace_car


# --- Positive tests ---


def test_build_returns_car_data(mock_builder, mock_ctx):
    ctx = mock_ctx()

    car = mock_builder.build(0, ctx)

    assert car["car_idx"] == 0
    assert car["car_number"] == "12"
    assert car["lap_dist_pct"] == pytest.approx(0.3)
    assert car["is_in_pitroad"] is False


@pytest.mark.parametrize(
    "username,expected",
    [
        ("PACE CAR", True),
        ("pace car", True),
        ("Driver1", False),
        ("", False),
    ],
)
def test_is_pace_car_variants(mock_builder, username, expected):
    driver = {"UserName": username}

    assert mock_builder._is_pace_car(driver) is expected


@pytest.mark.parametrize(
    "driver,expected",
    [
        ({"UserName": "Driver1", "CarIsPaceCar": 1}, True),
        ({"UserName": "Safety Car", "CarIsPaceCar": 1}, True),
        ({"UserName": "Pace Car", "CarIsPaceCar": 0}, True),
        ({"UserName": "Driver1", "CarIsPaceCar": 0}, False),
        ({}, False),
    ],
)
def test_is_pace_car_by_flag_or_name(driver, expected):
    assert is_pace_car(driver) is expected


def test_build_returns_none_for_pace_car_flag(mock_builder, mock_ctx):
    ctx = mock_ctx(
        drivers=[{"UserName": "Safety", "CarNumber": "0", "CarIsPaceCar": 1}],
        lap_dist_pct=[0.0],
        is_pitroad=[False],
        positions=[0],
        class_positions=[0],
    )

    assert mock_builder.build(0, ctx) is None


@pytest.mark.parametrize(
    "drivers,expected",
    [
        ([{"CarClassID": 1}, {"CarClassID": 1}], False),
        ([{"CarClassID": 1}, {"CarClassID": 2}], True),
        # The pace car has its own class id, which must not count.
        (
            [
                {"CarClassID": 5},
                {"CarClassID": 5},
                {"UserName": "Pace Car", "CarClassID": 11, "CarIsPaceCar": 1},
            ],
            False,
        ),
        # Entries without a class id are ignored.
        ([{"CarClassID": 1}, {"CarClassID": None}, {}], False),
        ([], False),
    ],
)
def test_is_multiclass(drivers, expected):
    assert is_multiclass(drivers) is expected


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
