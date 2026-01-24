from backend.services.leaderboard.service import CarSorter


def test_car_sorter_orders_correctly():
    cars = [
        {"pos": 3},
        {"pos": None},
        {"pos": 1},
        {"pos": 0},
    ]
    result = CarSorter.sort(cars)
    assert [c["pos"] for c in result] == [1, 3, 0, None]
