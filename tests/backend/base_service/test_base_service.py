import pytest


# --- Positive tests ---


def test_session_state_context_fields(mock_ctx):
    ctx = mock_ctx()

    assert ctx.multiclass is False
    assert len(ctx.drivers) == 2
    assert ctx.positions == [1, 2]
    assert ctx.class_positions == [0, 1]
    assert ctx.lap_dist_pct == [0.3, 0.6]
    assert ctx.is_pitroad == [False, True]


def test_get_snapshot_calls_build_snapshot_when_context_exists(
    mock_service, mock_ctx
):
    ctx = mock_ctx()
    mock_service._build_context = lambda: ctx
    mock_service._build_snapshot = lambda c: {
        "status": "ok",
        "cars": [c.drivers[0]["CarNumber"]],
    }

    result = mock_service.get_snapshot()

    assert result["status"] == "ok"
    assert "12" in result["cars"]


def test_empty_snapshot_returns_correct_structure(mock_service):
    result = mock_service._empty_snapshot()
    assert isinstance(result, dict)
    assert result["status"] == "waiting"
    assert result["cars"] == []


# --- Negative tests ---


def test_get_snapshot_returns_empty_when_context_is_none(mock_service):
    mock_service._build_context = lambda: None

    result = mock_service.get_snapshot()

    assert result == {
        "status": "waiting",
        "cars": [],
    }


def test_build_context_not_implemented(mock_service):
    with pytest.raises(NotImplementedError):
        mock_service._build_context()


def test_build_snapshot_not_implemented(mock_service, mock_ctx):
    ctx = mock_ctx()
    with pytest.raises(NotImplementedError):
        mock_service._build_snapshot(ctx)
