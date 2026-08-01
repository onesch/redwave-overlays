"""
iRacing iRating calculator.

Original algorithm based on the iRacing rating calculation formula.
Calculations based on:
https://github.com/SIMRacingApps/SIMRacingApps/files/3617438/iRacing.SOF.iRating.Calculator.v1_1.xlsx
"""

from __future__ import annotations

import math
from typing import Mapping


LN_2 = 0.693147180559945309417232121458176568
BASE_RATING = 1600 / LN_2


def calculate_win_probability(
    rating_a: float,
    rating_b: float,
    factor: float = BASE_RATING,
) -> float:
    """
    Calculate probability of driver A beating driver B.

    Args:
        rating_a: First driver's iRating.
        rating_b: Second driver's iRating.
        factor: Scaling factor.

    Returns:
        Probability value.
    """

    exp_a = math.exp(-rating_a / factor)
    exp_b = math.exp(-rating_b / factor)

    quality_a = (1 - exp_a) * exp_b
    quality_b = (1 - exp_b) * exp_a

    return quality_a / (quality_b + quality_a)


class IRatingCalculator:
    """
    Calculates iRating changes after a race.

    Input order must represent final race positions.
    """

    def calculate(
        self,
        race_results: Mapping[str, int],
    ) -> dict[str, int]:
        """
        Calculate iRating delta for each driver.

        Args:
            race_results:
                Mapping where:
                - key is driver identifier
                - value is starting iRating.

                Order represents finishing positions.

        Returns:
            Mapping:
                {
                    driver_id: irating_delta,
                }
        """

        drivers = list(race_results.items())
        total_drivers = len(drivers)

        expected_scores = []

        for _, rating in drivers:
            expected = -0.5

            for _, opponent_rating in drivers:
                expected += calculate_win_probability(
                    rating,
                    opponent_rating,
                )

            expected_scores.append(expected)

        deltas = {}

        for position, ((driver_id, _), expected) in enumerate(
            zip(drivers, expected_scores),
            start=1,
        ):
            change = (
                total_drivers
                - position
                - expected
                - ((total_drivers / 2) - position) / 100
            ) * 200 / total_drivers

            deltas[driver_id] = round(change)

        return deltas

    @staticmethod
    def calculate_sof(
        race_results: Mapping[str, int],
    ) -> int:
        """
        Calculate Strength of Field.

        Args:
            race_results:
                Mapping of driver identifiers to starting iRatings.

        Returns:
            SOF value.
        """

        if not race_results:
            return 0

        total = sum(
            math.exp(-rating / BASE_RATING)
            for rating in race_results.values()
        )

        return round(
            -BASE_RATING
            * math.log(total / len(race_results))
        )


race = {
    "Driver 1": 3945,
    "Driver 2": 1221,
    "Driver 3": 1322,
    "Driver 4": 1321,
    "Meeeee 5": 1479,
    "Driver 6": 1626,
    "Driver 7": 1371,
    "Driver 8": 1448,
    "Driver 9": 1348,
}

calculator = IRatingCalculator()

new_ratings = calculator.calculate(race)

race_sof = calculator.calculate_sof(race)
print(race_sof)

for driver, rating in new_ratings.items():
    print(driver, rating)
