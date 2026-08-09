import pytest

from backend.utils.irating_calculation import (
    IRatingCalculator,
    calculate_win_probability,
)


@pytest.mark.parametrize(
    "rating_a,rating_b,expected",
    [
        (2000, 2000, 0.5),
        (2000, 1800, 0.5385630371161682),
        (1800, 2000, 0.4614369628838318),
    ],
)
def test_calculate_win_probability(rating_a, rating_b, expected):
    result = calculate_win_probability(rating_a, rating_b)

    assert result == pytest.approx(expected)


def test_calculate_win_probability_is_complementary():
    driver_a = calculate_win_probability(2200, 1600)
    driver_b = calculate_win_probability(1600, 2200)

    assert driver_a + driver_b == pytest.approx(1.0)


@pytest.mark.parametrize(
    "race_results,expected_deltas",
    [
        ({1: 2000, 2: 1800, 3: 1700}, {1: 60, 2: 2, 3: -60}),
        ({1: 1000, 2: 2000}, {1: 72, 2: -71}),
        ({2: 1800}, {2: 1}),
    ],
)
def test_irating_calculator_calculates_deltas(race_results, expected_deltas):
    calculator = IRatingCalculator()

    result = calculator.calculate(race_results)

    assert result == expected_deltas


@pytest.mark.parametrize(
    "race_results,expected_sof",
    [
        ({}, 0),
        ({1: 2000, 2: 1800, 3: 1700}, 1830),
        ({1: 1000, 2: 2000}, 1446),
    ],
)
def test_irating_calculator_calculates_sof(race_results, expected_sof):
    calculator = IRatingCalculator()

    result = calculator.calculate_sof(race_results)

    assert result == expected_sof
