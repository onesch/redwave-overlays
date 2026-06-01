import pytest


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
def test_is_valid_lap_time(mock_lap_times, lap_time, expected):
    assert mock_lap_times.is_valid_lap_time(lap_time) is expected


def test_fastest_lap_ignores_invalid_values(mock_lap_times):
    VALUES = [0, None, 81.2, "80", 79]
    assert mock_lap_times.fastest_lap(VALUES) == pytest.approx(79.0)


def test_fastest_lap_returns_none_without_valid_values(mock_lap_times):
    VALUES = [0, None, "80", -1]
    assert mock_lap_times.fastest_lap(VALUES) is None


def test_session_and_class_fastest_lap(mock_lap_times, mock_ctx):
    ctx = mock_ctx(
        best_lap_times=[82.0, 79.5, 90.0, 0],
        drivers=[
            {"CarClassID": 1},
            {"CarClassID": 1},
            {"CarClassID": 2},
            {"CarClassID": 2},
        ],
    )

    assert mock_lap_times.session_fastest_lap(ctx) == pytest.approx(79.5)
    assert mock_lap_times.class_fastest_lap(ctx, 1) == pytest.approx(79.5)
    assert mock_lap_times.class_fastest_lap(ctx, 2) == pytest.approx(90.0)


def test_car_lap_time_returns_best_or_estimated(mock_lap_times, mock_ctx):
    ctx = mock_ctx(
        best_lap_times=[79.5, 0, None],
        drivers=[
            {"CarClassEstLapTime": 82.0},
            {"CarClassEstLapTime": 83.0},
            {"CarClassEstLapTime": "invalid"},
        ],
    )

    assert mock_lap_times.car_lap_time(0, ctx) == pytest.approx(79.5)
    assert mock_lap_times.car_lap_time(1, ctx) == pytest.approx(83.0)
    assert mock_lap_times.car_lap_time(2, ctx) is None


@pytest.mark.parametrize(
    "current_session,player_lap_time,expected",
    [
        ({"SessionLaps": "unlimited", "SessionType": "Race"}, 80.0, None),
        ({"SessionLaps": 10, "SessionType": "Practice"}, 80.0, None),
        ({"SessionLaps": 10, "SessionType": "Race"}, None, None),
        ({"SessionLaps": 10, "SessionType": "Race"}, 80.0, 800.0),
    ],
)
def test_calculate_session_time_based_on_laps(
    mock_lap_times,
    current_session,
    player_lap_time,
    expected,
):
    assert (
        mock_lap_times.calculate_session_time_based_on_laps(
            current_session,
            player_lap_time,
        )
        == expected
    )
