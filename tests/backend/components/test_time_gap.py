import pytest

from backend.components.time_gap import TimeGapComponent
from backend.components.track_position import CarPositionContext


@pytest.fixture
def time_gap() -> TimeGapComponent:
    return TimeGapComponent()


def make_cars(**overrides) -> tuple[CarPositionContext, CarPositionContext]:
    """The reference and the target car; by default of one class and model."""
    values = {
        "reference_dist": 0.2,
        "target_dist": 0.5,
        "reference_est_time": 16.0,
        "target_est_time": 40.0,
        "reference_est_lap_time": 80.0,
        "target_est_lap_time": 80.0,
        "reference_class": 1,
        "target_class": 1,
    }
    values.update(overrides)

    reference = CarPositionContext(
        lap_dist_pct=values["reference_dist"],
        est_time=values["reference_est_time"],
        est_lap_time=values["reference_est_lap_time"],
        class_id=values["reference_class"],
    )
    target = CarPositionContext(
        lap_dist_pct=values["target_dist"],
        est_time=values["target_est_time"],
        est_lap_time=values["target_est_lap_time"],
        class_id=values["target_class"],
    )
    return reference, target


class FixedTimeLine:
    """A time line that answers every gap with one value."""

    def __init__(self, gap):
        self.gap = gap
        self.calls = []

    def time_between(self, reference_dist, target_dist):
        self.calls.append((reference_dist, target_dist))
        return self.gap


# --- time_gap: time line ---


@pytest.mark.parametrize("target_class", [1, 2])
def test_time_gap_prefers_the_time_line_for_every_car(time_gap, target_class):
    reference, target = make_cars(target_class=target_class)
    time_line = FixedTimeLine(0.25)

    assert time_gap.time_gap(reference, target, time_line) == pytest.approx(0.25)
    assert time_line.calls == [(0.2, 0.5)]


@pytest.mark.parametrize(
    "time_line,target_class,expected",
    [
        # No time line data at the points: same class -> CarIdxEstTime.
        (FixedTimeLine(None), 1, 24.0),
        # No time line data at the points: another class -> distance.
        (FixedTimeLine(None), 2, 24.0),
        # No time line at all.
        (None, 1, 24.0),
    ],
)
def test_time_gap_falls_back_without_time_line_data(
    time_gap,
    time_line,
    target_class,
    expected,
):
    # Same class: 40.0 - 16.0 = 24.0; another class: 0.3 lap * 80.0 = 24.0.
    reference, target = make_cars(target_class=target_class)

    assert time_gap.time_gap(reference, target, time_line) == pytest.approx(expected)


def test_time_gap_without_known_classes_uses_the_distance(time_gap):
    # Unknown classes are not the same class: CarIdxEstTime is not trusted.
    reference, target = make_cars(
        reference_class=None,
        target_class=None,
        target_est_time=70.0,
    )

    assert time_gap.time_gap(reference, target) == pytest.approx(24.0)


# --- time_gap: same class without the time line ---


def test_time_gap_same_class_uses_estimated_time(time_gap):
    assert time_gap.time_gap(*make_cars()) == pytest.approx(24.0)


def test_time_gap_same_class_rescales_another_car_model(time_gap):
    # GT3 at Le Mans: a car model with a 1% slower reference lap level with
    # the player. Its CarIdxEstTime is 1% larger; rescaled, the gap is 0.
    reference, target = make_cars(
        reference_est_time=115.0,
        target_est_time=116.15,
        reference_est_lap_time=230.0,
        target_est_lap_time=232.3,
    )

    assert time_gap.time_gap(reference, target) == pytest.approx(0.0, abs=1e-9)


def test_time_gap_same_class_without_target_lap_time_is_not_rescaled(time_gap):
    reference, target = make_cars(target_est_lap_time=None)

    assert time_gap.time_gap(reference, target) == pytest.approx(24.0)


@pytest.mark.parametrize(
    "reference_dist,target_dist,expected",
    [
        (0.98, 0.02, 4.0),
        (0.02, 0.98, -4.0),
    ],
)
def test_time_gap_same_class_corrects_start_finish_wraparound(
    time_gap,
    reference_dist,
    target_dist,
    expected,
):
    reference, target = make_cars(
        reference_dist=reference_dist,
        target_dist=target_dist,
        reference_est_time=reference_dist * 100,
        target_est_time=target_dist * 100,
        reference_est_lap_time=100.0,
        target_est_lap_time=100.0,
    )

    assert time_gap.time_gap(reference, target) == pytest.approx(expected)


def test_time_gap_same_class_without_lap_times_is_not_wrapped(time_gap):
    # The gap is still known, but cannot be rescaled or wrapped.
    reference, target = make_cars(
        reference_est_time=2.0,
        target_est_time=98.0,
        reference_est_lap_time=0.0,
        target_est_lap_time=None,
    )

    assert time_gap.time_gap(reference, target) == pytest.approx(96.0)


@pytest.mark.parametrize(
    "field,value",
    [
        ("reference_est_time", 0),
        ("reference_est_time", -1),
        ("reference_est_time", None),
        ("target_est_time", 0),
        ("target_est_time", -1),
        ("target_est_time", None),
    ],
)
def test_time_gap_same_class_without_estimated_time_returns_none(
    time_gap,
    field,
    value,
):
    assert time_gap.time_gap(*make_cars(**{field: value})) is None


# --- time_gap: another class without the time line ---


@pytest.mark.parametrize(
    "target_dist,expected",
    [
        (0.5016, 0.18),
        (0.4969, -0.36),
        (0.5, 0.0),
    ],
)
def test_time_gap_other_class_uses_distance_at_reference_pace(
    time_gap,
    target_dist,
    expected,
):
    reference, target = make_cars(
        reference_dist=0.5,
        target_dist=target_dist,
        reference_est_lap_time=115.25,
        target_class=2,
    )

    assert time_gap.time_gap(reference, target) == pytest.approx(
        expected, abs=0.01
    )


def test_time_gap_other_class_ignores_estimated_time(time_gap):
    # Formation lap snapshot: a car of another class level with the player
    # had a rescaled CarIdxEstTime gap of 0.32 s.
    reference, target = make_cars(
        reference_dist=0.06,
        target_dist=0.06,
        reference_est_time=6.9,
        target_est_time=5.0,
        reference_est_lap_time=115.25,
        target_est_lap_time=141.2,
        target_class=2,
    )

    assert time_gap.time_gap(reference, target) == pytest.approx(0.0)


@pytest.mark.parametrize(
    "field,value",
    [
        ("target_dist", -1),
        ("reference_dist", None),
        ("reference_est_lap_time", 0),
        ("reference_est_lap_time", None),
    ],
)
def test_time_gap_other_class_without_data_returns_none(time_gap, field, value):
    reference, target = make_cars(**{field: value}, target_class=2)

    assert time_gap.time_gap(reference, target) is None
