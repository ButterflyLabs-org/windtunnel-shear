"""Tests for core data models."""

from __future__ import annotations

import json

from windtunnel_shear.core.models import (
    Episode,
    FaultInjectedError,
    HookAction,
    HookError,
    HookResult,
    InterceptedRequest,
    InterceptedResponse,
    ReplayMissError,
    Session,
    ShearError,
    Turn,
    TurnType,
    UpstreamError,
)

# ---------------------------------------------------------------------------
# InterceptedRequest
# ---------------------------------------------------------------------------


class TestInterceptedRequest:
    def test_basic_accessors(self, sample_raw_request: dict) -> None:
        req = InterceptedRequest(raw=sample_raw_request, timestamp=1.0)
        assert req.model == "gpt-4o"
        assert len(req.messages) == 2
        assert req.temperature == 0.7
        assert req.stream is False
        assert req.tools == []

    def test_messages_setter(self, sample_raw_request: dict) -> None:
        req = InterceptedRequest(raw=sample_raw_request, timestamp=1.0)
        new_msgs = [{"role": "user", "content": "Hello"}]
        req.messages = new_msgs
        assert req.messages == new_msgs
        assert req.raw["messages"] == new_msgs

    def test_empty_raw(self) -> None:
        req = InterceptedRequest(raw={}, timestamp=0.0)
        assert req.model == ""
        assert req.messages == []
        assert req.tools == []
        assert req.stream is False
        assert req.temperature is None

    def test_is_tool_result_false(self, sample_raw_request: dict) -> None:
        req = InterceptedRequest(raw=sample_raw_request, timestamp=1.0)
        assert req.is_tool_result is False

    def test_is_tool_result_true(self, sample_tool_call_request: dict) -> None:
        req = InterceptedRequest(raw=sample_tool_call_request, timestamp=1.0)
        assert req.is_tool_result is True

    def test_pending_tool_calls(self, sample_tool_call_request: dict) -> None:
        req = InterceptedRequest(raw=sample_tool_call_request, timestamp=1.0)
        pending = req.pending_tool_calls
        assert len(pending) == 1
        assert pending[0]["function"]["name"] == "get_weather"

    def test_pending_tool_calls_empty(self, sample_raw_request: dict) -> None:
        req = InterceptedRequest(raw=sample_raw_request, timestamp=1.0)
        assert req.pending_tool_calls == []

    def test_tool_call_count(self, sample_tool_call_request: dict) -> None:
        req = InterceptedRequest(raw=sample_tool_call_request, timestamp=1.0)
        assert req.tool_call_count == 1

    def test_tool_call_count_zero(self, sample_raw_request: dict) -> None:
        req = InterceptedRequest(raw=sample_raw_request, timestamp=1.0)
        assert req.tool_call_count == 0

    def test_normalization_strips_fields(self) -> None:
        raw = {
            "model": "gpt-4o",
            "messages": [{"role": "user", "content": "hi"}],
            "stream": True,
            "user": "test-user",
            "temperature": 0.5,
        }
        req = InterceptedRequest(raw=raw, timestamp=0.0)
        normed = req.normalized()
        assert "stream" not in normed
        assert "user" not in normed
        assert normed["model"] == "gpt-4o"
        assert normed["messages"] == [{"role": "user", "content": "hi"}]
        assert normed["temperature"] == 0.5

    def test_compute_hash_deterministic(self) -> None:
        raw = {"model": "gpt-4o", "messages": [{"role": "user", "content": "hi"}]}
        req1 = InterceptedRequest(raw=dict(raw), timestamp=0.0)
        req2 = InterceptedRequest(raw=dict(raw), timestamp=99.0)
        h1 = req1.compute_hash()
        h2 = req2.compute_hash()
        assert h1 == h2
        assert len(h1) == 16
        assert req1.request_hash == h1

    def test_compute_hash_different_content(self) -> None:
        req1 = InterceptedRequest(
            raw={"model": "gpt-4o", "messages": [{"role": "user", "content": "hello"}]},
            timestamp=0.0,
        )
        req2 = InterceptedRequest(
            raw={"model": "gpt-4o", "messages": [{"role": "user", "content": "world"}]},
            timestamp=0.0,
        )
        assert req1.compute_hash() != req2.compute_hash()


# ---------------------------------------------------------------------------
# InterceptedResponse
# ---------------------------------------------------------------------------


class TestInterceptedResponse:
    def test_basic_accessors(self, sample_raw_response: dict) -> None:
        resp = InterceptedResponse(raw=sample_raw_response, status_code=200)
        assert resp.content == "The capital of France is Paris."
        assert resp.finish_reason == "stop"
        assert resp.usage["total_tokens"] == 33
        assert resp.has_tool_calls is False
        assert resp.is_shear_injected is False

    def test_content_setter(self, sample_raw_response: dict) -> None:
        resp = InterceptedResponse(raw=sample_raw_response)
        resp.content = "Modified content."
        assert resp.content == "Modified content."
        assert resp.raw["choices"][0]["message"]["content"] == "Modified content."

    def test_empty_response(self) -> None:
        resp = InterceptedResponse(raw={})
        assert resp.content == ""
        assert resp.finish_reason == ""
        assert resp.usage == {}
        assert resp.choices == []
        assert resp.tool_calls == []
        assert resp.has_tool_calls is False

    def test_tool_calls(self, sample_tool_call_response: dict) -> None:
        resp = InterceptedResponse(raw=sample_tool_call_response)
        assert resp.has_tool_calls is True
        assert len(resp.tool_calls) == 1
        assert resp.tool_calls[0]["function"]["name"] == "get_weather"
        assert resp.finish_reason == "tool_calls"

    def test_shear_injected(self) -> None:
        resp = InterceptedResponse(
            raw={"choices": []},
            status_code=429,
            reason="shear:fault:rate_limit:0.3",
        )
        assert resp.is_shear_injected is True

    def test_not_shear_injected(self, sample_raw_response: dict) -> None:
        resp = InterceptedResponse(raw=sample_raw_response, reason="")
        assert resp.is_shear_injected is False


# ---------------------------------------------------------------------------
# Turn / Episode / Session
# ---------------------------------------------------------------------------


class TestTurnType:
    def test_values(self) -> None:
        assert TurnType.USER_MESSAGE.value == "user_message"
        assert TurnType.TOOL_CALL_REQUEST.value == "tool_call_request"
        assert TurnType.TOOL_RESULT_SUBMISSION.value == "tool_result_submission"
        assert TurnType.FINAL_RESPONSE.value == "final_response"

    def test_string_comparison(self) -> None:
        assert TurnType.USER_MESSAGE == "user_message"


class TestEpisode:
    def test_empty_episode(self) -> None:
        ep = Episode(episode_id="test")
        assert ep.tool_call_count == 0
        assert ep.total_tokens == 0
        assert ep.turns == []

    def test_episode_with_turns(
        self,
        intercepted_request: InterceptedRequest,
        intercepted_response: InterceptedResponse,
    ) -> None:
        turn = Turn(
            turn_type=TurnType.USER_MESSAGE,
            request=intercepted_request,
            response=intercepted_response,
        )
        ep = Episode(episode_id="ep1", turns=[turn])
        assert ep.total_tokens == 33
        assert len(ep.turns) == 1

    def test_auto_generated_id(self) -> None:
        ep1 = Episode()
        ep2 = Episode()
        assert ep1.episode_id != ep2.episode_id
        assert len(ep1.episode_id) == 12


class TestSession:
    def test_empty_session(self) -> None:
        sess = Session(session_id="test")
        assert sess.total_turns == 0
        assert sess.total_tokens == 0
        assert sess.episodes == []

    def test_session_aggregation(self, sample_session: Session) -> None:
        assert sample_session.total_turns == 1
        assert sample_session.total_tokens == 33
        assert sample_session.model == "gpt-4o"

    def test_to_json_structure(self, sample_session: Session) -> None:
        data = sample_session.to_json()
        assert data["session_id"] == "sess-001"
        assert data["model"] == "gpt-4o"
        assert data["shear_version"] == "0.1.0"
        assert data["summary"]["total_turns"] == 1
        assert data["summary"]["total_tokens"] == 33
        assert len(data["episodes"]) == 1
        assert len(data["episodes"][0]["turns"]) == 1

    def test_roundtrip_serialization(self, sample_session: Session) -> None:
        data = sample_session.to_json()
        # Ensure it's valid JSON
        json_str = json.dumps(data)
        parsed = json.loads(json_str)
        restored = Session.from_json(parsed)
        assert restored.session_id == sample_session.session_id
        assert restored.model == sample_session.model
        assert restored.total_turns == sample_session.total_turns
        assert restored.total_tokens == sample_session.total_tokens
        assert len(restored.episodes) == 1
        assert restored.episodes[0].episode_id == "ep-001"

    def test_from_json_empty(self) -> None:
        sess = Session.from_json({})
        assert sess.session_id == ""
        assert sess.total_turns == 0

    def test_auto_generated_id(self) -> None:
        s1 = Session()
        s2 = Session()
        assert s1.session_id != s2.session_id


# ---------------------------------------------------------------------------
# HookAction / HookResult
# ---------------------------------------------------------------------------


class TestHookAction:
    def test_values(self) -> None:
        assert HookAction.ALLOW.value == "allow"
        assert HookAction.MODIFY.value == "modify"
        assert HookAction.BLOCK.value == "block"
        assert HookAction.SIMULATE.value == "simulate"


class TestHookResult:
    def test_allow_result(self) -> None:
        result = HookResult(action=HookAction.ALLOW)
        assert result.request is None
        assert result.response is None
        assert result.reason == ""

    def test_block_result(self) -> None:
        result = HookResult(action=HookAction.BLOCK, reason="Policy violation")
        assert result.action == HookAction.BLOCK
        assert result.reason == "Policy violation"


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------


class TestExceptions:
    def test_shear_error_hierarchy(self) -> None:
        assert issubclass(HookError, ShearError)
        assert issubclass(ReplayMissError, ShearError)
        assert issubclass(UpstreamError, ShearError)
        assert issubclass(FaultInjectedError, ShearError)

    def test_hook_error_message(self) -> None:
        original = ValueError("bad value")
        err = HookError("my_hook", original, "hooks.py", 42)
        assert "my_hook" in str(err)
        assert "hooks.py:42" in str(err)
        assert "ValueError" in str(err)
        assert err.hook_name == "my_hook"
        assert err.original is original

    def test_replay_miss_error(self) -> None:
        err = ReplayMissError("abc123", "def456", "model mismatch")
        assert "abc123" in str(err)
        assert "def456" in str(err)
        assert "model mismatch" in str(err)

    def test_upstream_error(self) -> None:
        err = UpstreamError(503, "Service Unavailable", "https://api.openai.com")
        assert err.status_code == 503
        assert "503" in str(err)

    def test_fault_injected_error(self) -> None:
        err = FaultInjectedError("rate_limit", "shear:fault:rate_limit:0.3")
        assert err.fault_type == "rate_limit"
        assert "rate_limit" in str(err)
