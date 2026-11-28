import pytest

from backend.components.lap_relation import LapRelationComponent

SAME_LAP = (False, False)
LAP_AHEAD = (True, False)
LAP_BEHIND = (False, True)


def lap_flags(**overrides) -> tuple[bool, bool]:
    """
    (is_lap_ahead, is_lap_behind) of car 1 relative to the reference car 0.
    """
    values = {
        "reference_laps": 5,
        "reference_dist": 0.5,
        "other_laps": 5,
        "other_dist": 0.6,
    }
    values.update(overrides)

    deltas = LapRelationComponent().compute(
        laps=[values["reference_laps"], values["other_laps"]],
        lap_dist_pct=[values["reference_dist"], values["other_dist"]],
        reference_idx=0,
    )
    delta = deltas.get(1)
    return (
        LapRelationComponent.is_lap_ahead(delta),
        LapRelationComponent.is_lap_behind(delta),
    )


# --- lap relation of a car ---


def test_same_lap():
    assert lap_flags() == SAME_LAP


def test_car_ahead_on_higher_lap():
    # The other car is more than half a lap up the road on the next lap.
    assert lap_flags(other_laps=6, other_dist=0.6) == LAP_AHEAD


def test_car_behind_on_lower_lap():
    # The other car is more than half a lap behind on the previous lap.
    assert lap_flags(other_laps=4, other_dist=0.4) == LAP_BEHIND


def test_car_ahead_across_start_finish_is_not_a_lap_ahead():
    # Lap counts differ only because the other car already crossed the line
    # while the reference car is still 0.02 lap before it.
    result = lap_flags(
        reference_laps=5,
        reference_dist=0.98,
        other_laps=6,
        other_dist=0.02,
    )
    assert result == SAME_LAP


def test_car_behind_across_start_finish_is_not_a_lap_behind():
    # Lap counts differ only because the reference car already crossed
    # the line while the other car is still 0.02 lap before it.
    result = lap_flags(
        reference_laps=6,
        reference_dist=0.02,
        other_laps=5,
        other_dist=0.98,
    )
    assert result == SAME_LAP


@pytest.mark.parametrize(
    "other_laps,other_dist,expected",
    [
        # A lap ahead while physically just behind: about to lap the car.
        (6, 0.45, LAP_AHEAD),
        # A lap behind while physically just ahead: being lapped.
        (4, 0.55, LAP_BEHIND),
    ],
)
def test_keeps_close_cars_on_adjacent_laps(other_laps, other_dist, expected):
    result = lap_flags(
        reference_laps=5,
        reference_dist=0.5,
        other_laps=other_laps,
        other_dist=other_dist,
    )
    assert result == expected


@pytest.mark.parametrize(
    "other_laps,other_dist,expected",
    [
        # A whole lap ahead and right next to the reference car.
        (7, 0.03, LAP_AHEAD),
        # A whole lap behind and right next to the reference car.
        (3, 0.03, LAP_BEHIND),
    ],
)
def test_keeps_whole_lap_at_start_finish(other_laps, other_dist, expected):
    result = lap_flags(
        reference_laps=5,
        reference_dist=0.02,
        other_laps=other_laps,
        other_dist=other_dist,
    )
    assert result == expected


# --- compute ---


def test_compute_returns_whole_lap_deltas_for_all_cars():
    deltas = LapRelationComponent().compute(
        laps=[5, 7, 5, 3],
        lap_dist_pct=[0.5, 0.6, 0.7, 0.4],
        reference_idx=0,
    )

    assert deltas == {1: 2, 2: 0, 3: -2}


def test_compute_excludes_reference_car():
    deltas = LapRelationComponent().compute(
        laps=[5, 5],
        lap_dist_pct=[0.5, 0.6],
        reference_idx=0,
    )

    assert 0 not in deltas


@pytest.mark.parametrize("dist", [-1, None, "bad"])
def test_compute_skips_cars_without_valid_distance(dist):
    deltas = LapRelationComponent().compute(
        laps=[5, 6, 4],
        lap_dist_pct=[0.5, dist, 0.4],
        reference_idx=0,
    )

    assert deltas == {2: -1}


def test_compute_skips_cars_missing_from_shorter_array():
    deltas = LapRelationComponent().compute(
        laps=[5, 6],
        lap_dist_pct=[0.5, 0.6, 0.7],
        reference_idx=0,
    )

    assert deltas == {1: 1}


@pytest.mark.parametrize(
    "laps,lap_dist_pct,reference_idx",
    [
        # The reference car is not on the track.
        ([5, 6], [-1, 0.6], 0),
        # No reference car.
        ([5, 6], [0.5, 0.6], None),
        # The reference index is out of range.
        ([5, 6], [0.5, 0.6], 99),
        ([5, 6], [0.5, 0.6], -1),
        # No telemetry.
        ([], [], 0),
    ],
)
def test_compute_returns_empty_relations_without_reference_position(
    laps,
    lap_dist_pct,
    reference_idx,
):
    deltas = LapRelationComponent().compute(
        laps=laps,
        lap_dist_pct=lap_dist_pct,
        reference_idx=reference_idx,
    )

    assert deltas == {}


# --- is_lap_ahead / is_lap_behind ---


@pytest.mark.parametrize(
    "delta,expected",
    [
        (2, LAP_AHEAD),
        (1, LAP_AHEAD),
        (0, SAME_LAP),
        (-1, LAP_BEHIND),
        (-3, LAP_BEHIND),
        # A car without a lap difference: unknown, not flagged.
        (None, SAME_LAP),
    ],
)
def test_lap_flags_from_delta(delta, expected):
    assert (
        LapRelationComponent.is_lap_ahead(delta),
        LapRelationComponent.is_lap_behind(delta),
    ) == expected
