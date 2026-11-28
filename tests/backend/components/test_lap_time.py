import pytest

from backend.components.lap_time import LapTimeComponent


@pytest.mark.parametrize(
    "lap_time,expected",
    [
        (80.0, True),
        (1, True),
        (0, False),
        (-1, False),
        (None, False),
        ("80", False),
    ],
)
def test_is_valid_lap_time(lap_time, expected):
    assert LapTimeComponent.is_valid_lap_time(lap_time) is expected


def test_fastest_lap_ignores_invalid_values():
    VALUES = [0, None, 81.2, "80", 79]
    assert LapTimeComponent.fastest_lap(VALUES) == pytest.approx(79.0)


def test_fastest_lap_returns_none_without_valid_values():
    VALUES = [0, None, "80", -1]
    assert LapTimeComponent.fastest_lap(VALUES) is None
