import pytest

from backend.components.pit_stop import PIT_EXIT_HOLD_SEC, PitStopComponent


def make_pit_stops(laps_started, is_pitroad, now=1000.0) -> PitStopComponent:
    pit_stops = PitStopComponent()
    pit_stops.update(laps_started=laps_started, is_pitroad=is_pitroad, now=now)
    return pit_stops


def test_car_never_in_the_pits_has_no_label():
    pit_stops = make_pit_stops(laps_started=[5], is_pitroad=[False])

    assert pit_stops.labels(now=1000.0) == {}


def test_car_on_the_pit_road_shows_the_lap_it_is_on():
    pit_stops = make_pit_stops(laps_started=[5, 3], is_pitroad=[True, False])

    assert pit_stops.labels(now=1000.0) == {0: "IN L5"}


def test_car_out_of_the_pits_shows_out_then_the_pit_lap():
    pit_stops = make_pit_stops(laps_started=[5], is_pitroad=[True], now=1000.0)

    # Back on the track on lap 6: the label keeps the lap of the stop.
    pit_stops.update(laps_started=[6], is_pitroad=[False], now=1010.0)
    assert pit_stops.labels(now=1010.0) == {0: "OUT L5"}

    pit_stops.update(laps_started=[6], is_pitroad=[False], now=1013.0)
    assert pit_stops.labels(now=1013.0) == {0: "OUT L5"}

    later = 1010.0 + PIT_EXIT_HOLD_SEC + 1
    pit_stops.update(laps_started=[6], is_pitroad=[False], now=later)
    assert pit_stops.labels(now=later) == {0: "L5"}


def test_out_label_lasts_exactly_the_hold_time():
    pit_stops = make_pit_stops(laps_started=[5], is_pitroad=[True])
    pit_stops.update(laps_started=[5], is_pitroad=[False], now=1000.0)

    assert pit_stops.labels(now=1000.0 + PIT_EXIT_HOLD_SEC) == {0: "OUT L5"}
    assert pit_stops.labels(now=1000.1 + PIT_EXIT_HOLD_SEC) == {0: "L5"}


def test_new_pit_stop_replaces_the_previous_one():
    pit_stops = make_pit_stops(laps_started=[5], is_pitroad=[True])
    pit_stops.update(laps_started=[6], is_pitroad=[False], now=1000.0)

    pit_stops.update(laps_started=[12], is_pitroad=[True], now=1500.0)
    assert pit_stops.labels(now=1500.0) == {0: "IN L12"}

    pit_stops.update(laps_started=[12], is_pitroad=[False], now=1520.0)
    assert pit_stops.labels(now=1520.0) == {0: "OUT L12"}


@pytest.mark.parametrize(
    "is_pitroad,now,expected",
    [
        # Lap 0 has no lap to show.
        (True, 1000.0, {0: "IN PIT"}),
        (False, 1000.0, {0: "OUT PIT"}),
        (False, 1000.0 + PIT_EXIT_HOLD_SEC + 1, {}),
    ],
)
def test_pit_stop_before_the_start_shows_pit(is_pitroad, now, expected):
    pit_stops = make_pit_stops(laps_started=[0], is_pitroad=[True])
    pit_stops.update(laps_started=[0], is_pitroad=[is_pitroad], now=1000.0)

    assert pit_stops.labels(now=now) == expected


def test_cars_missing_from_either_array_are_skipped():
    pit_stops = make_pit_stops(laps_started=[5], is_pitroad=[True, True])

    assert pit_stops.labels(now=1000.0) == {0: "IN L5"}


def test_clear_forgets_all_pit_stops():
    pit_stops = make_pit_stops(laps_started=[5, 7], is_pitroad=[True, True])

    pit_stops.clear()

    assert pit_stops.labels(now=1000.0) == {}
    # A car that was in the pits before the clear gets no "OUT" label.
    pit_stops.update(laps_started=[5, 7], is_pitroad=[False, False], now=1001.0)
    assert pit_stops.labels(now=1001.0) == {}
