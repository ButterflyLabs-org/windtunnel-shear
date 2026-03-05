"""Tests for session recording and episode grouping."""

from __future__ import annotations

from windtunnel_shear.core.models import (
    InterceptedRequest,
    InterceptedResponse,
)
from windtunnel_shear.core.session import SessionRecorder


def _req(content: str = "hi", has_tool_result: bool = False) -> InterceptedRequest:
    messages: list[dict[str, str]] = []
    if has_tool_result:
        messages.append({"role": "tool", "content": "result"})
    messages.append({"role": "user", "content": content})
    return InterceptedRequest(raw={"model": "gpt-4o", "messages": messages})


def _resp(
    content: str = "hello",
    finish_reason: str = "stop",
    tool_calls: bool = False,
) -> InterceptedResponse:
    msg: dict[str, object] = {"role": "assistant", "content": content}
    if tool_calls:
        msg["tool_calls"] = [
            {"id": "1", "function": {"name": "get_weather", "arguments": "{}"}},
        ]
    return InterceptedResponse(
        raw={
            "choices": [{"message": msg, "finish_reason": finish_reason}],
            "usage": {"total_tokens": 10},
        },
        status_code=200,
    )


class TestSessionRecorder:
    def test_single_turn(self) -> None:
        rec = SessionRecorder()
        rec.record_turn(_req(), _resp())
        session = rec.finalize()
        assert session.total_turns == 1
        assert len(session.episodes) == 1

    def test_model_captured(self) -> None:
        rec = SessionRecorder()
        rec.record_turn(_req(), _resp())
        assert rec.session.model == "gpt-4o"

    def test_request_hash_computed(self) -> None:
        rec = SessionRecorder()
        req = _req()
        rec.record_turn(req, _resp())
        assert req.request_hash != ""

    def test_multiple_turns_same_episode(self) -> None:
        """Tool call loop stays in one episode."""
        rec = SessionRecorder()
        rec.record_turn(_req("call tool"), _resp(tool_calls=True, finish_reason="tool_calls"))
        rec.record_turn(_req("result", has_tool_result=True), _resp())
        session = rec.finalize()
        assert len(session.episodes) == 1
        assert session.total_turns == 2

    def test_new_episode_after_final(self) -> None:
        """New user message after final response starts new episode."""
        rec = SessionRecorder()
        rec.record_turn(_req("first"), _resp("answer1"))
        rec.record_turn(_req("second"), _resp("answer2"))
        session = rec.finalize()
        assert len(session.episodes) == 2

    def test_session_serialization(self) -> None:
        rec = SessionRecorder()
        rec.record_turn(_req(), _resp())
        session = rec.finalize()
        data = session.to_json()
        assert data["summary"]["total_turns"] == 1
        assert data["model"] == "gpt-4o"

    def test_started_at_set(self) -> None:
        rec = SessionRecorder()
        assert rec.session.started_at != ""
