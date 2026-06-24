from typing import Any, Dict, List


class CarSorter:
    """Utility class for sorting car data dictionaries."""

    @staticmethod
    def sort(cars: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Sort cars by position, keeping None or 0 at the end."""
        return sorted(
            cars,
            key=lambda c: (
                c["pos"] is None or c["pos"] == 0,
                c["pos"] if isinstance(c["pos"], int) else 9999,
            ),
        )
