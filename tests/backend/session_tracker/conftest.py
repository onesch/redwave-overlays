import pytest

from backend.services.session_tracker import (
    SessionKey,
    SessionTracker,
)


@pytest.fixture
def mock_tracker() -> SessionTracker:
    """
    Returns an initialized SessionTracker object.
    """

    return SessionTracker()


@pytest.fixture
def mock_key():
    """
    Factory for creating SessionKey instances.
    """

    def _make_key(session_id=1, session_num=1):
        return SessionKey(
            session_id=session_id,
            session_num=session_num,
        )

    return _make_key
