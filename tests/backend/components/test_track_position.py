import pytest

from backend.components.track_position import TrackPositionComponent


# --- is_on_track ---


@pytest.mark.parametrize(
    "value,expected",
    [
        (0, True),
        (0.5, True),
        (-1, False),
        (None, False),
        ("abc", False),
    ],
)
def test_is_on_track(value, expected):
    assert TrackPositionComponent.is_on_track(value) is expected


# --- distance_gap ---


@pytest.mark.parametrize(
    "reference_dist,target_dist,expected",
    [
        (0.2, 0.5, 0.3),
        (0.45, 0.47, 0.02),
        (0.47, 0.45, -0.02),
        # Close cars across the start/finish line.
        (0.98, 0.02, 0.04),
        (0.02, 0.98, -0.04),
        # More than half a lap up the road is closer from behind.
        (0.1, 0.7, -0.4),
        (0.7, 0.1, 0.4),
        # The same position.
        (0.5, 0.5, 0.0),
    ],
)
def test_distance_gap_returns_shortest_signed_gap(
    reference_dist,
    target_dist,
    expected,
):
    assert TrackPositionComponent.distance_gap(
        reference_dist, target_dist
    ) == pytest.approx(expected)


@pytest.mark.parametrize("dist", [-1, None, "abc"])
def test_distance_gap_without_valid_distance_returns_none(dist):
    assert TrackPositionComponent.distance_gap(0.5, dist) is None
    assert TrackPositionComponent.distance_gap(dist, 0.5) is None


# --- wrap_to_nearest_lap ---


@pytest.mark.parametrize(
    "value,lap,expected",
    [
        # Lap distance.
        (0.3, 1.0, 0.3),
        (-0.96, 1.0, 0.04),
        (0.96, 1.0, -0.04),
        (0.6, 1.0, -0.4),
        # Seconds.
        (-96.0, 100.0, 4.0),
        (96.0, 100.0, -4.0),
        (30.0, 100.0, 30.0),
        # Whole laps are removed.
        (2.25, 1.0, 0.25),
    ],
)
def test_wrap_to_nearest_lap(value, lap, expected):
    assert TrackPositionComponent.wrap_to_nearest_lap(value, lap) == pytest.approx(
        expected
    )
