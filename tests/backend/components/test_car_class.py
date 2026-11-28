import pytest

from backend.components.car_class import CarClassComponent


# --- is_pace_car ---


@pytest.mark.parametrize(
    "driver,expected",
    [
        ({"UserName": "PACE CAR"}, True),
        ({"UserName": "pace car"}, True),
        ({"UserName": "Safety Car", "CarIsPaceCar": 1}, True),
        ({"UserName": "Pace Car", "CarIsPaceCar": 0}, True),
        ({"UserName": "Driver1", "CarIsPaceCar": 0}, False),
        ({"UserName": ""}, False),
        ({}, False),
    ],
)
def test_is_pace_car_by_flag_or_name(driver, expected):
    assert CarClassComponent.is_pace_car(driver) is expected


# --- is_multiclass ---


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
    assert CarClassComponent.is_multiclass(drivers) is expected


# --- is_same_class ---


@pytest.mark.parametrize(
    "reference_class_id,target_class_id,expected",
    [
        (1, 1, True),
        (1, 2, False),
        (1, None, False),
        (None, 1, False),
        (None, None, False),
    ],
)
def test_is_same_class(reference_class_id, target_class_id, expected):
    assert CarClassComponent.is_same_class(
        reference_class_id, target_class_id
    ) is expected
