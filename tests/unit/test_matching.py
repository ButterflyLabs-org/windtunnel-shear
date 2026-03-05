"""Tests for replay matching strategies."""

from __future__ import annotations

import pytest

from windtunnel_shear.core.matching import (
    ExactMatcher,
    SequentialMatcher,
    create_matcher,
)
from windtunnel_shear.core.models import (
    Episode,
    InterceptedRequest,
    InterceptedResponse,
    ReplayMissError,
    Session,
    Turn,
    TurnType,
)


def _build_session(n_turns: int = 3) -> Session:
    """Build a session with n_turns for testing."""
    turns = []
    for i in range(n_turns):
        req = InterceptedRequest(
            raw={"model": "gpt-4o", "messages": [{"role": "user", "content": f"q{i}"}]},
        )
        req.compute_hash()
        resp = InterceptedResponse(
            raw={
                "choices": [
                    {"message": {"content": f"a{i}"}, "finish_reason": "stop"},
                ],
                "usage": {"total_tokens": 10},
            },
            status_code=200,
        )
        turns.append(Turn(turn_type=TurnType.USER_MESSAGE, request=req, response=resp))

    return Session(episodes=[Episode(turns=turns)])


class TestSequentialMatcher:
    def test_returns_in_order(self) -> None:
        session = _build_session(3)
        matcher = SequentialMatcher(session)
        for i in range(3):
            req = InterceptedRequest(
                raw={"model": "gpt-4o", "messages": [{"role": "user", "content": "any"}]},
            )
            resp = matcher.match(req)
            assert resp.content == f"a{i}"

    def test_exhausted_raises(self) -> None:
        session = _build_session(1)
        matcher = SequentialMatcher(session)
        req = InterceptedRequest(
            raw={"model": "gpt-4o", "messages": []},
        )
        matcher.match(req)  # consume the one turn
        with pytest.raises(ReplayMissError, match="exhausted"):
            matcher.match(req)

    def test_empty_session(self) -> None:
        session = Session(episodes=[])
        matcher = SequentialMatcher(session)
        req = InterceptedRequest(raw={"messages": []})
        with pytest.raises(ReplayMissError):
            matcher.match(req)


class TestExactMatcher:
    def test_match_by_hash(self) -> None:
        session = _build_session(3)
        matcher = ExactMatcher(session)

        # Build a request with the same content as q1
        req = InterceptedRequest(
            raw={"model": "gpt-4o", "messages": [{"role": "user", "content": "q1"}]},
        )
        resp = matcher.match(req)
        assert resp.content == "a1"

    def test_miss_raises(self) -> None:
        session = _build_session(1)
        matcher = ExactMatcher(session)
        req = InterceptedRequest(
            raw={"model": "gpt-4o", "messages": [{"role": "user", "content": "unknown"}]},
        )
        with pytest.raises(ReplayMissError, match="No recorded response"):
            matcher.match(req)


class TestCreateMatcher:
    def test_sequential(self) -> None:
        session = _build_session(1)
        matcher = create_matcher(session, "sequential")
        assert isinstance(matcher, SequentialMatcher)

    def test_exact(self) -> None:
        session = _build_session(1)
        matcher = create_matcher(session, "exact")
        assert isinstance(matcher, ExactMatcher)

    def test_unknown_mode(self) -> None:
        session = _build_session(1)
        with pytest.raises(ValueError, match="Unknown match mode"):
            create_matcher(session, "fuzzy")
