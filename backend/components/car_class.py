from typing import Any


class CarClassComponent:
    """
    Car classes of a session: the pace car, multiclass sessions and whether
    two cars race in the same class.
    """

    @staticmethod
    def is_pace_car(driver: dict) -> bool:
        """
        Return True when a DriverInfo.Drivers entry is the pace car.

        iRacing flags the pace car with CarIsPaceCar; older sessions only
        name it "Pace Car". The pace car has its own car class, so it is left
        out of class calculations and the leaderboard.

        Example:

            is_pace_car({"CarIsPaceCar": 1})                      -> True
            is_pace_car({"UserName": "Pace Car"})                 -> True
            is_pace_car({"UserName": "Driver 1", "CarIsPaceCar": 0}) -> False

        Args:
            driver: A DriverInfo.Drivers entry.

        Returns:
            True if flagged by CarIsPaceCar or named "Pace Car".
        """
        return bool(driver.get("CarIsPaceCar")) or (
            driver.get("UserName", "").upper() == "PACE CAR"
        )

    @classmethod
    def is_multiclass(cls, drivers: list[dict]) -> bool:
        """
        Return True when the session has more than one car class.

        The pace car and entries without a class id are not counted.

        Example:

            CarClassID of the drivers:

            [4074, 4074, 4074]               -> False    # GT3 only
            [4074, 4074, 2523]               -> True     # GT3 and LMP2
            [4074, 4074, 11 (pace car)]      -> False

        Args:
            drivers: DriverInfo.Drivers entries.

        Returns:
            True if more than one CarClassID is present.
        """
        class_ids = {
            driver.get("CarClassID")
            for driver in drivers
            if driver.get("CarClassID") and not cls.is_pace_car(driver)
        }
        return len(class_ids) > 1

    @staticmethod
    def is_same_class(reference_class_id: Any, target_class_id: Any) -> bool:
        """
        Return True when two cars are in the same, known car class.

        A car with an unknown class is never in the same class: calculations
        that rely on cars sharing the class (TimeGapComponent) must not
        trust it.

        Example:

            is_same_class(4074, 4074) -> True
            is_same_class(4074, 2523) -> False
            is_same_class(4074, None) -> False
            is_same_class(None, None) -> False

        Args:
            reference_class_id: Car class of the reference car (CarClassID).
            target_class_id: Car class of the target car (CarClassID).

        Returns:
            False when either class is unknown.
        """
        return (
            reference_class_id is not None
            and target_class_id is not None
            and reference_class_id == target_class_id
        )
