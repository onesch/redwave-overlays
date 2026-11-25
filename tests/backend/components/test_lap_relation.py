import pytest

from backend.components.lap_relation import (
    LapRelationComponent,
    LapRelations,
    wrap_gap,
)


def lap_label(**overrides):
    """
    Lap relation label of car 1 relative to the reference car 0.
    """
    values = {
        "reference_laps": 5,
        "reference_dist": 0.5,
        "other_laps": 5,
        "other_dist": 0.6,
    }
    values.update(overrides)

    relations = LapRelationComponent().compute(
        laps=[values["reference_laps"], values["other_laps"]],
        lap_dist_pct=[values["reference_dist"], values["other_dist"]],
        reference_idx=0,
    )
    return relations.label(1)


# --- wrap_gap ---


@pytest.mark.parametrize(
    "raw_gap,expected",
    [
        (0.3, 0.3),
        (-0.3, -0.3),
        # Close cars across the start/finish line.
        (0.96, -0.04),
        (-0.96, 0.04),
        (1.2, 0.2),
    ],
)
def test_wrap_gap_returns_shortest_signed_gap(raw_gap, expected):
    assert wrap_gap(raw_gap) == pytest.approx(expected)


# --- lap relation labels ---


def test_same_lap_returns_none():
    assert lap_label() is None


def test_car_ahead_on_higher_lap():
    # The other car is more than half a lap up the road on the next lap.
    assert lap_label(other_laps=6, other_dist=0.6) == "ahead_lap"


def test_car_behind_on_lower_lap():
    # The other car is more than half a lap behind on the previous lap.
    assert lap_label(other_laps=4, other_dist=0.4) == "behind_lap"


def test_car_ahead_across_start_finish_is_not_a_lap_ahead():
    # Lap counts differ only because the other car already crossed the line
    # while the reference car is still 0.02 lap before it.
    result = lap_label(
        reference_laps=5,
        reference_dist=0.98,
        other_laps=6,
        other_dist=0.02,
    )
    assert result is None


def test_car_behind_across_start_finish_is_not_a_lap_behind():
    # Lap counts differ only because the reference car already crossed
    # the line while the other car is still 0.02 lap before it.
    result = lap_label(
        reference_laps=6,
        reference_dist=0.02,
        other_laps=5,
        other_dist=0.98,
    )
    assert result is None


@pytest.mark.parametrize(
    "other_laps,other_dist,expected",
    [
        # A lap ahead while physically just behind: about to lap the car.
        (6, 0.45, "ahead_lap"),
        # A lap behind while physically just ahead: being lapped.
        (4, 0.55, "behind_lap"),
    ],
)
def test_keeps_close_cars_on_adjacent_laps(other_laps, other_dist, expected):
    result = lap_label(
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
        (7, 0.03, "ahead_lap"),
        # A whole lap behind and right next to the reference car.
        (3, 0.03, "behind_lap"),
    ],
)
def test_keeps_whole_lap_at_start_finish(other_laps, other_dist, expected):
    result = lap_label(
        reference_laps=5,
        reference_dist=0.02,
        other_laps=other_laps,
        other_dist=other_dist,
    )
    assert result == expected


# --- compute ---


def test_compute_returns_whole_lap_deltas_for_all_cars():
    relations = LapRelationComponent().compute(
        laps=[5, 7, 5, 3],
        lap_dist_pct=[0.5, 0.6, 0.7, 0.4],
        reference_idx=0,
    )

    assert relations.deltas == {1: 2, 2: 0, 3: -2}
    assert relations.label(1) == "ahead_lap"
    assert relations.label(2) is None
    assert relations.label(3) == "behind_lap"


def test_compute_excludes_reference_car():
    relations = LapRelationComponent().compute(
        laps=[5, 5],
        lap_dist_pct=[0.5, 0.6],
        reference_idx=0,
    )

    assert relations.delta(0) is None
    assert relations.label(0) is None


@pytest.mark.parametrize("dist", [-1, None, "bad"])
def test_compute_skips_cars_without_valid_distance(dist):
    relations = LapRelationComponent().compute(
        laps=[5, 6, 4],
        lap_dist_pct=[0.5, dist, 0.4],
        reference_idx=0,
    )

    assert relations.delta(1) is None
    assert relations.delta(2) == -1


def test_compute_skips_cars_missing_from_shorter_array():
    relations = LapRelationComponent().compute(
        laps=[5, 6],
        lap_dist_pct=[0.5, 0.6, 0.7],
        reference_idx=0,
    )

    assert relations.deltas == {1: 1}


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
    relations = LapRelationComponent().compute(
        laps=laps,
        lap_dist_pct=lap_dist_pct,
        reference_idx=reference_idx,
    )

    assert relations == LapRelations()


# --- LapRelations ---


def test_empty_relations_return_none():
    relations = LapRelations()

    assert relations.delta(0) is None
    assert relations.label(0) is None
