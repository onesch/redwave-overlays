import pytest

from backend.components.track_position import CarPositionContext
from backend.components.track_time_line import (
    MAX_INTERPOLATION_SPAN,
    SEGMENTS_PER_LAP,
    TrackTimeLineComponent,
)

LAP_TIME = 100.0


def segment_center(segment: int) -> float:
    return (segment + 0.5) / SEGMENTS_PER_LAP


def car(lap_dist_pct, est_time, est_lap_time=LAP_TIME) -> CarPositionContext:
    return CarPositionContext(
        lap_dist_pct=lap_dist_pct,
        est_time=est_time,
        est_lap_time=est_lap_time,
    )


def make_time_line(est_lap_time=LAP_TIME, track_id="track") -> TrackTimeLineComponent:
    time_line = TrackTimeLineComponent()
    time_line.bind(track_id, 1, est_lap_time)
    return time_line


def filled_time_line(est_lap_time: float = LAP_TIME) -> TrackTimeLineComponent:
    """The time line of a car driving the lap at a constant pace."""
    time_line = make_time_line(est_lap_time)
    for segment in range(SEGMENTS_PER_LAP):
        pct = segment_center(segment)
        time_line.record(car(pct, pct * est_lap_time, est_lap_time))
    return time_line


# --- time_at ---


def test_empty_time_line_has_no_time():
    assert make_time_line().time_at(0.5) is None


def test_time_at_interpolates_between_filled_segments():
    time_line = make_time_line()
    time_line.record(car(segment_center(500), 50.0))
    time_line.record(car(segment_center(502), 51.0))

    assert time_line.time_at(segment_center(501)) == pytest.approx(50.5)
    assert time_line.time_at(segment_center(500)) == pytest.approx(50.0)


def test_time_at_averages_samples_of_one_segment():
    time_line = make_time_line()
    time_line.record(car(segment_center(500), 49.0))
    time_line.record(car(segment_center(500), 51.0))
    time_line.record(car(segment_center(501), 52.0))

    assert time_line.time_at(segment_center(500)) == pytest.approx(50.0)


def test_time_at_needs_data_on_both_sides():
    # Data only behind the point: not extrapolated, the caller falls back.
    time_line = make_time_line()
    time_line.record(car(segment_center(498), 49.8))
    time_line.record(car(segment_center(499), 49.9))

    assert time_line.time_at(segment_center(501)) is None


def test_time_at_does_not_bridge_wide_holes():
    time_line = make_time_line()
    time_line.record(car(segment_center(500), 50.0))
    time_line.record(car(segment_center(500 + MAX_INTERPOLATION_SPAN + 1), 50.6))

    assert time_line.time_at(segment_center(502)) is None


@pytest.mark.parametrize("dist", [-1, 1.0, None, "abc"])
def test_time_at_invalid_distance_returns_none(dist):
    assert filled_time_line().time_at(dist) is None


# --- record ---


def test_record_rescales_samples_to_the_time_line_lap_time():
    # A car model with a 2% slower reference lap: its CarIdxEstTime runs
    # 2% slower at every point and is brought to the time line's car pace.
    time_line = make_time_line(est_lap_time=100.0)
    time_line.record(car(segment_center(500), 51.0, 102.0))
    time_line.record(car(segment_center(501), 51.102, 102.0))

    assert time_line.time_at(segment_center(500)) == pytest.approx(50.0)


def test_record_mixes_car_models_into_one_time_line():
    time_line = make_time_line(est_lap_time=100.0)
    # Two car models of one class at neighbouring points.
    time_line.record(car(segment_center(500), 50.0, 100.0))
    time_line.record(car(segment_center(501), 51.612, 102.0))  # 50.6 at the time line's pace

    # Halfway between the two samples, both at the time line's pace.
    assert time_line.time_at(0.501) == pytest.approx(50.3)


@pytest.mark.parametrize(
    "dist,est,est_lap_time",
    [
        (-1, 10.0, LAP_TIME),
        (1.0, 10.0, LAP_TIME),
        (None, 10.0, LAP_TIME),
        (0.5, 0, LAP_TIME),
        (0.5, -1, LAP_TIME),
        (0.5, None, LAP_TIME),
        (0.5, 50.0, 0),
        (0.5, 50.0, None),
    ],
)
def test_record_ignores_invalid_samples(dist, est, est_lap_time):
    time_line = make_time_line()
    time_line.record(car(dist, est, est_lap_time))

    assert time_line._sample_counts == [0] * SEGMENTS_PER_LAP


@pytest.mark.parametrize("est_lap_time", [0, -1, None])
def test_record_without_time_line_lap_time_is_ignored(est_lap_time):
    time_line = make_time_line(est_lap_time=est_lap_time)
    time_line.record(car(0.5, 50.0))

    assert time_line._sample_counts == [0] * SEGMENTS_PER_LAP


# --- time_between ---


@pytest.mark.parametrize(
    "reference_dist,target_dist,expected",
    [
        (0.20, 0.25, 5.0),
        (0.25, 0.20, -5.0),
        # Across the start/finish line.
        (0.98, 0.02, 4.0),
        (0.02, 0.98, -4.0),
    ],
)
def test_time_between_reads_the_time_line(reference_dist, target_dist, expected):
    gap = filled_time_line().time_between(reference_dist, target_dist)

    assert gap == pytest.approx(expected, abs=0.01)


def test_time_between_follows_the_speed_profile():
    # Slow in the first half of the lap and fast in the second:
    # the same distance takes different time depending on where it is.
    time_line = make_time_line()
    for segment in range(SEGMENTS_PER_LAP):
        pct = segment_center(segment)
        time = pct * 120 if pct < 0.5 else 60 + (pct - 0.5) * 80
        time_line.record(car(pct, time))

    assert time_line.time_between(0.20, 0.25) == pytest.approx(6.0, abs=0.01)
    assert time_line.time_between(0.70, 0.75) == pytest.approx(4.0, abs=0.01)


def test_time_between_is_ordered_like_the_cars_on_the_track():
    time_line = filled_time_line()
    gaps = [time_line.time_between(0.5, 0.5 + d) for d in (0.001, 0.002, 0.003, 0.004)]

    assert gaps == sorted(gaps)


def test_time_between_without_time_line_data_returns_none():
    time_line = make_time_line()
    time_line.record(car(segment_center(200), 20.0))
    time_line.record(car(segment_center(201), 20.1))

    assert time_line.time_between(segment_center(200), 0.7) is None


def test_time_between_without_binding_returns_none():
    assert TrackTimeLineComponent().time_between(0.2, 0.25) is None


# --- bind ---


def test_bind_keeps_the_time_line_for_the_same_binding():
    time_line = filled_time_line()
    time_line.bind("track", 1, LAP_TIME)

    assert time_line.time_at(0.5) == pytest.approx(50.0)


@pytest.mark.parametrize(
    "track_id,class_id,est_lap_time",
    [
        ("other_track", 1, LAP_TIME),
        ("track", 2, LAP_TIME),
        ("track", 1, LAP_TIME + 1),
    ],
)
def test_bind_clears_the_time_line_on_a_new_track_class_or_car(
    track_id,
    class_id,
    est_lap_time,
):
    time_line = filled_time_line()
    time_line.bind(track_id, class_id, est_lap_time)

    assert time_line.time_at(0.5) is None
