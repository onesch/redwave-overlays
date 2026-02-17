import pytest


def test_session_key_is_immutable(mock_key):
    key = mock_key()

    with pytest.raises(Exception):
        key.session_id = 2


def test_is_changed_returns_false_if_session_id_is_none(
    mock_tracker, mock_key
):
    key = mock_key(session_id=None)

    assert mock_tracker.is_changed(key) is False


def test_is_changed_returns_false_if_session_num_is_none(
    mock_tracker, mock_key
):
    key = mock_key(session_num=None)

    assert mock_tracker.is_changed(key) is False


def test_is_changed_returns_true_on_first_valid_key(
    mock_tracker, mock_key
):
    key = mock_key()

    assert mock_tracker.is_changed(key) is True


def test_is_changed_returns_false_for_same_key(
    mock_tracker, mock_key
):
    key = mock_key()

    assert mock_tracker.is_changed(key) is True
    assert mock_tracker.is_changed(key) is False


def test_is_changed_returns_true_when_session_id_changes(
    mock_tracker, mock_key
):
    first = mock_key(session_id=1, session_num=1)
    second = mock_key(session_id=2, session_num=1)

    assert mock_tracker.is_changed(first) is True
    assert mock_tracker.is_changed(second) is True


def test_is_changed_returns_true_when_session_num_changes(
    mock_tracker, mock_key
):
    first = mock_key(session_id=1, session_num=1)
    second = mock_key(session_id=1, session_num=2)

    assert mock_tracker.is_changed(first) is True
    assert mock_tracker.is_changed(second) is True


def test_invalid_key_does_not_override_last_key(
    mock_tracker, mock_key
):
    valid = mock_key()
    invalid = mock_key(session_id=None, session_num=None)

    assert mock_tracker.is_changed(valid) is True
    assert mock_tracker.is_changed(invalid) is False
    assert mock_tracker.is_changed(valid) is False
