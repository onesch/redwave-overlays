from typing import Protocol, Any


class ILeaderboardParser(Protocol):
    """
    interface/Protocol for Leaderboard service, which
    requires only part of IRSDKParser functionality.

    Leaderboard service -> ILeaderboardParser (requires only part)
    -> IRSDKParser -> IRSDKService -> irsdk.IRSDK
    """

    # declared with self for typing; actually a @staticmethod in IRSDKParser
    def normalize_color(self, value: Any) -> str | None: ...
