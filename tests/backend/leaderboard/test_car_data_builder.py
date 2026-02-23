import pytest

from backend.services.leaderboard.service import CarDataBuilder


# --- CarDataBuilder tests ---


def test_builder_returns_none_for_pace_car(mock_ctx, mock_builder):
    ctx = mock_ctx(drivers=[{"UserName": "PACE CAR"}])

    result = mock_builder.build(0, ctx)
    assert result is None


def test_reset_pit_data_clears_dicts(mock_builder):
    mock_builder._last_pit_laps = {0: 5}
    mock_builder._pit_exit_times = {0: 1234567890.0}

    mock_builder.reset_pit_data()

    assert mock_builder._last_pit_laps == {}
    assert mock_builder._pit_exit_times == {}


@pytest.mark.parametrize(
    "username,expected",
    [
        ("PACE CAR", True),
        ("pace car", True),
        ("PaCe CaR", True),
        ("Driver1", False),
        ("", False),
    ],
)
def test_is_pace_car_variants(mock_values, username, expected):
    mock_builder = CarDataBuilder(mock_values)
    driver = {"UserName": username}
    assert mock_builder._is_pace_car(driver) is expected


@pytest.mark.parametrize(
    "username,expected",
    [
        ("Driver One", "Driver"),
        (" SingleName ", "SingleName"),
        ("", ""),
        ("   ", ""),
    ],
)
def test_get_first_name_variants(mock_values, username, expected):
    mock_builder = CarDataBuilder(mock_values)
    driver = {"UserName": username}
    assert mock_builder._get_first_name(driver) == expected


@pytest.mark.parametrize(
    "lap_dist,expected",
    [
        (0.4567, 0.457),
        (0.0, 0.0),
        (-0.1, None),
        (None, None),
        ("not_float", None),
    ],
)
def test_format_lap_dist_variants(mock_builder, mock_ctx, lap_dist, expected):
    ctx = mock_ctx(lap_dist_pct=[lap_dist])
    assert mock_builder._format_lap_dist(0, ctx) == expected


def test_resolve_position_multiclass_zero_and_negative(mock_builder, mock_ctx):
    ctx = mock_ctx(positions=[0, -1])
    zero_pos = mock_builder._resolve_position(idx=0, ctx=ctx)
    negative_pos = mock_builder._resolve_position(idx=1, ctx=ctx)
    assert zero_pos == 1
    assert negative_pos is None


def test_resolve_position_normal_and_negative(mock_builder, mock_ctx):
    ctx = mock_ctx(positions=[-1, 3])
    assert mock_builder._resolve_position(0, ctx) is None
    assert mock_builder._resolve_position(1, ctx) == 3


def test_get_starting_position_from_qualify_stats(mock_builder):
    pos = mock_builder._get_starting_position(
        car_idx=1, field="Position", offset=0
    )
    assert pos == 2


def test_get_starting_position_missing_qualify(mock_builder):
    pos = mock_builder._get_starting_position(
        car_idx=999, field="Position", offset=0
    )
    assert pos == 0


def test_starting_position_falls_back_to_race(mock_builder, mock_ctx):
    ctx = mock_ctx(positions=[0])
    result = mock_builder.build(0, ctx)
    assert result["name"] == "Driver1"
    assert result["pos"] == 1


def test_builder_converts_negative_position_to_none(mock_builder, mock_ctx):
    NEGATIVE_TO_NONE = -1
    ctx = mock_ctx(positions=[NEGATIVE_TO_NONE])
    result = mock_builder.build(0, ctx)
    assert result["pos"] is None


def test_builder_negative_laps_converted_to_zero(mock_builder, mock_ctx):
    CONVERTED_TO_ZERO = -999
    ctx = mock_ctx(laps_started=[CONVERTED_TO_ZERO])
    result = mock_builder.build(0, ctx)
    assert result["laps_started"] == 0


def test_builder_negative_lap_dist_pct_to_none(mock_builder, mock_ctx):
    NEGATIVE_TO_NONE = -9.9
    ctx = mock_ctx(lap_dist_pct=[NEGATIVE_TO_NONE])
    result = mock_builder.build(0, ctx)
    assert result["lap_dist_pct"] is None


def test_builder_returns_valid_data(mock_builder, mock_ctx):
    ctx = mock_ctx()
    result = mock_builder.build(0, ctx)

    assert result["pos"] == 1
    assert result["car_idx"] == 0
    assert result["car_number"] == "12"
    assert result["name"] == "Driver1"
    assert result["laps_started"] == 5
    assert result["last_lap"] == "01:20.000"
    assert result["irating"] == 2000
    assert result["license"] == "A 4.99"
    assert result["car_class_color"] == 16711680
    assert result["lap_dist_pct"] == 0.6


def test_get_last_pit_lap_behavior(mock_builder):
    laps_started = [5, 6]
    is_pitroad = [True, False]

    result_in = mock_builder._get_last_pit_lap(0, laps_started, is_pitroad)
    assert result_in == "IN L5"

    mock_builder._last_pit_laps[1] = 6
    result_out_first = mock_builder._get_last_pit_lap(
        1, laps_started, [False, False]
    )
    assert result_out_first.startswith("OUT L6")

    mock_builder._pit_exit_times[1] -= 6
    result_after = mock_builder._get_last_pit_lap(
        1, laps_started, [False, False]
    )
    assert result_after == "L6"


def test_build_all_returns_all_cars_except_excluded(mock_builder, mock_ctx):
    ctx = mock_ctx()

    cars = mock_builder.build_all(ctx, exclude_idx=0)

    assert isinstance(cars, list)
    assert len(cars) == 2
    assert all(car["car_idx"] != 0 for car in cars)


def test_build_all_without_exclude_returns_all(mock_builder, mock_ctx):
    ctx = mock_ctx()

    cars = mock_builder.build_all(ctx)

    assert len(cars) == len(ctx.drivers)


def test_build_all_filters_pace_car(mock_builder, mock_ctx):
    ctx = mock_ctx(
        drivers=[
            {"UserName": "PACE CAR"},
            {"UserName": "Driver1"},
        ],
    )

    cars = mock_builder.build_all(ctx)

    assert len(cars) == 1
    assert cars[0]["name"] == "Driver1"


def test_build_all_sorted_by_position(mock_builder, mock_ctx):
    ctx = mock_ctx(positions=[3, 1, 2])

    cars = mock_builder.build_all(ctx)

    positions = [car["pos"] for car in cars]
    assert positions == sorted(positions)
