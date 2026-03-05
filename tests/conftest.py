"""Shared test fixtures for windtunnel-shear."""

from __future__ import annotations

import pytest

from windtunnel_shear.core.models import (
    Episode,
    InterceptedRequest,
    InterceptedResponse,
    Session,
    Turn,
    TurnType,
)


@pytest.fixture()
def sample_raw_request() -> dict:
    """A minimal OpenAI-compatible chat completion request body."""
    return {
        "model": "gpt-4o",
        "messages": [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "What is the capital of France?"},
        ],
        "temperature": 0.7,
        "max_tokens": 100,
        "stream": False,
    }


@pytest.fixture()
def sample_raw_response() -> dict:
    """A minimal OpenAI-compatible chat completion response body."""
    return {
        "id": "chatcmpl-abc123",
        "object": "chat.completion",
        "model": "gpt-4o",
        "choices": [
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": "The capital of France is Paris.",
                },
                "finish_reason": "stop",
            }
        ],
        "usage": {
            "prompt_tokens": 25,
            "completion_tokens": 8,
            "total_tokens": 33,
        },
    }


@pytest.fixture()
def sample_tool_call_request() -> dict:
    """A request body containing tool call results."""
    return {
        "model": "gpt-4o",
        "messages": [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "What's the weather in Paris?"},
            {
                "role": "assistant",
                "content": None,
                "tool_calls": [
                    {
                        "id": "call_abc123",
                        "type": "function",
                        "function": {
                            "name": "get_weather",
                            "arguments": '{"location": "Paris"}',
                        },
                    }
                ],
            },
            {
                "role": "tool",
                "tool_call_id": "call_abc123",
                "content": '{"temperature": 22, "condition": "sunny"}',
            },
        ],
        "tools": [
            {
                "type": "function",
                "function": {
                    "name": "get_weather",
                    "description": "Get weather for a location.",
                    "parameters": {
                        "type": "object",
                        "properties": {"location": {"type": "string"}},
                    },
                },
            }
        ],
    }


@pytest.fixture()
def sample_tool_call_response() -> dict:
    """A response body containing tool calls."""
    return {
        "id": "chatcmpl-def456",
        "object": "chat.completion",
        "model": "gpt-4o",
        "choices": [
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": None,
                    "tool_calls": [
                        {
                            "id": "call_xyz789",
                            "type": "function",
                            "function": {
                                "name": "get_weather",
                                "arguments": '{"location": "London"}',
                            },
                        }
                    ],
                },
                "finish_reason": "tool_calls",
            }
        ],
        "usage": {"prompt_tokens": 50, "completion_tokens": 20, "total_tokens": 70},
    }


@pytest.fixture()
def intercepted_request(sample_raw_request: dict) -> InterceptedRequest:
    """A ready-to-use InterceptedRequest."""
    return InterceptedRequest(raw=sample_raw_request, timestamp=1000.0)


@pytest.fixture()
def intercepted_response(sample_raw_response: dict) -> InterceptedResponse:
    """A ready-to-use InterceptedResponse."""
    return InterceptedResponse(
        raw=sample_raw_response,
        status_code=200,
        timestamp=1001.2,
        latency_ms=1200.0,
    )


@pytest.fixture()
def sample_session(
    intercepted_request: InterceptedRequest,
    intercepted_response: InterceptedResponse,
) -> Session:
    """A session with one episode containing one turn."""
    turn = Turn(
        turn_type=TurnType.USER_MESSAGE,
        request=intercepted_request,
        response=intercepted_response,
    )
    episode = Episode(episode_id="ep-001", turns=[turn])
    return Session(
        session_id="sess-001",
        model="gpt-4o",
        started_at="2026-01-01T00:00:00Z",
        episodes=[episode],
    )
