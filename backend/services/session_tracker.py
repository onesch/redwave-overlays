from dataclasses import dataclass


@dataclass(frozen=True)
class SessionKey:
    """
    Immutable identifier representing a unique iRacing session.

    Attributes:
        session_id (int | None):
            Logical session identifier from WeekendInfo.SessionID.
        session_num (int | None):
            Runtime session index from SessionNum
            (changes when switching sessions).

    Used by SessionTracker to detect session changes and trigger state resets.
    """

    session_id: int
    session_num: int


class SessionTracker:
    """
    Stateful helper responsible for detecting session changes.

    Maintains the previously observed SessionKey and determines
    if the current session differs from the last known one.
    """

    def __init__(self):
        self._last_key: SessionKey | None = None

    def is_changed(self, key: SessionKey) -> bool:
        """
        Determine if the session has changed.
        True if the session is considered changed, False otherwise.

        Rules:
            - If session_id or session_num is None, returns False.
            - If no previous key exists, returns True.
            - If the key differs from the previous one, returns True.
            - Otherwise, returns False.
        """
        if key.session_id is None or key.session_num is None:
            return False

        if self._last_key != key:
            self._last_key = key
            return True

        return False
