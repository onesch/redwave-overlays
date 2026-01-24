import pytest
from backend.services.leaderboard.service import TimeFormatter


@pytest.mark.parametrize(
    "seconds,expected",
    [
        (75.123, "01:15.123"),
        (0, "--:--.---"),
        (None, "--:--.---"),
    ],
)
def test_format_lap_time(seconds, expected):
    assert TimeFormatter.format_lap_time(seconds) == expected


@pytest.mark.parametrize(
    "secs,expected",
    [
        (None, "--:--.---"),
        (-5, "--:--.---"),
        (0, "00:00m"),
        (3600, "01:00:00h"),
        (3665, "01:01:05h"),
        (65, "01:05m"),
    ],
)
def test_format_session_time(secs, expected):
    assert (
        TimeFormatter.format_session_time(secs, is_seconds=True) == expected
    )
