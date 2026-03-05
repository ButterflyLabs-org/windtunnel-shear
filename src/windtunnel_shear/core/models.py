"""Data models for intercepted LLM API requests and responses.

This module defines the core data structures used throughout windtunnel-shear:
- InterceptedRequest / InterceptedResponse: Raw passthrough with typed accessors
- Turn / Episode / Session: Conversation structure for recording and replay
- HookAction / HookResult: Hook pipeline control flow
- Custom exception hierarchy
"""

from __future__ import annotations

import hashlib
import json
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, ClassVar

# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------


class ShearError(Exception):
    """Base exception for all windtunnel-shear errors."""


class HookError(ShearError):
    """A hook raised an exception during execution."""

    def __init__(self, hook_name: str, original: Exception, source_file: str = "", line: int = 0):
        self.hook_name = hook_name
        self.original = original
        self.source_file = source_file
        self.line = line
        location = f" ({source_file}:{line})" if source_file else ""
        super().__init__(
            f"Hook '{hook_name}'{location} raised {type(original).__name__}: {original}"
        )


class ReplayMissError(ShearError):
    """No matching recorded response found for the incoming request."""

    def __init__(self, request_hash: str, expected_hash: str = "", detail: str = ""):
        self.request_hash = request_hash
        self.expected_hash = expected_hash
        self.detail = detail
        msg = f"Replay miss: request hash={request_hash}"
        if expected_hash:
            msg += f", expected hash={expected_hash}"
        if detail:
            msg += f" — {detail}"
        super().__init__(msg)


class UpstreamError(ShearError):
    """The real upstream LLM API returned an error."""

    def __init__(self, status_code: int, body: str = "", upstream_url: str = ""):
        self.status_code = status_code
        self.body = body
        self.upstream_url = upstream_url
        super().__init__(f"Upstream error {status_code} from {upstream_url}: {body[:200]}")


class FaultInjectedError(ShearError):
    """Shear intentionally returned an error via fault injection."""

    def __init__(self, fault_type: str, reason: str = ""):
        self.fault_type = fault_type
        self.reason = reason
        super().__init__(f"Fault injected: {fault_type}" + (f" — {reason}" if reason else ""))


# ---------------------------------------------------------------------------
# Request / Response
# ---------------------------------------------------------------------------

# Fields stripped during request normalization for replay matching.
_NORMALIZATION_STRIP_FIELDS: set[str] = {
    "stream",
    "user",
    "seed",
    "logprobs",
    "top_logprobs",
    "n",
    "presence_penalty",
    "frequency_penalty",
    "logit_bias",
    "response_format",
    "service_tier",
    "store",
    "metadata",
}


@dataclass
class InterceptedRequest:
    """Raw LLM API request with typed accessors.

    The ``raw`` dict holds the complete request body — fields are never dropped.
    Typed properties provide convenient, type-safe access to common fields while
    reading from and writing back to ``raw``.

    Args:
        raw: Complete raw request body as a dict.
        timestamp: Monotonic timestamp when the request was captured.
        request_hash: Computed after normalization; used for replay matching.
    """

    raw: dict[str, Any]
    timestamp: float = field(default_factory=time.monotonic)
    request_hash: str = ""
    jitter_log: list[str] = field(default_factory=list)

    # -- Typed accessors ----------------------------------------------------

    @property
    def messages(self) -> list[dict[str, Any]]:
        """Message array from the request body."""
        result: list[dict[str, Any]] = self.raw.get("messages", [])
        return result

    @messages.setter
    def messages(self, value: list[dict[str, Any]]) -> None:
        self.raw["messages"] = value

    @property
    def model(self) -> str:
        """Target model identifier."""
        result: str = self.raw.get("model", "")
        return result

    @property
    def tools(self) -> list[dict[str, Any]]:
        """Tool definitions attached to the request."""
        result: list[dict[str, Any]] = self.raw.get("tools", [])
        return result

    @property
    def stream(self) -> bool:
        """Whether the request asks for streaming."""
        result: bool = self.raw.get("stream", False)
        return result

    @property
    def temperature(self) -> float | None:
        """Sampling temperature, if set."""
        return self.raw.get("temperature")

    # -- Agent-aware accessors ----------------------------------------------

    @property
    def is_tool_result(self) -> bool:
        """True if this request contains tool result messages."""
        return any(m.get("role") == "tool" for m in self.messages)

    @property
    def pending_tool_calls(self) -> list[dict[str, Any]]:
        """Tool calls from the most recent assistant message."""
        for msg in reversed(self.messages):
            if msg.get("role") == "assistant" and msg.get("tool_calls"):
                result: list[dict[str, Any]] = msg["tool_calls"]
                return result
        return []

    @property
    def tool_call_count(self) -> int:
        """Total tool calls observed across the entire message history."""
        count = 0
        for msg in self.messages:
            if msg.get("role") == "assistant" and msg.get("tool_calls"):
                count += len(msg["tool_calls"])
        return count

    # -- Normalization & hashing --------------------------------------------

    def normalized(self) -> dict[str, Any]:
        """Return a copy of ``raw`` with non-deterministic fields stripped.

        Used for computing a stable hash for replay matching.

        Returns:
            A new dict with only deterministic fields preserved.
        """
        return {k: v for k, v in self.raw.items() if k not in _NORMALIZATION_STRIP_FIELDS}

    def compute_hash(self) -> str:
        """Compute and store a stable hash of the normalized request body.

        Returns:
            The hex-digest hash string.
        """
        payload = json.dumps(self.normalized(), sort_keys=True, ensure_ascii=False)
        self.request_hash = hashlib.sha256(payload.encode()).hexdigest()[:16]
        return self.request_hash


@dataclass
class InterceptedResponse:
    """Raw LLM API response with typed accessors.

    Args:
        raw: Complete raw response body as a dict.
        status_code: HTTP status code.
        timestamp: Monotonic timestamp when the response was captured.
        latency_ms: Round-trip latency in milliseconds.
        reason: Non-empty when the response was injected by Shear (fault/simulation).
    """

    raw: dict[str, Any]
    status_code: int = 200
    timestamp: float = 0.0
    latency_ms: float = 0.0
    reason: str = ""

    @property
    def choices(self) -> list[dict[str, Any]]:
        """Choices array from the response body."""
        result: list[dict[str, Any]] = self.raw.get("choices", [])
        return result

    @property
    def content(self) -> str:
        """First choice message content."""
        if self.choices and self.choices[0].get("message"):
            result: str = self.choices[0]["message"].get("content", "")
            return result
        return ""

    @content.setter
    def content(self, value: str) -> None:
        if self.choices and self.choices[0].get("message"):
            self.choices[0]["message"]["content"] = value

    @property
    def usage(self) -> dict[str, int]:
        """Token usage dict from the response body."""
        result: dict[str, int] = self.raw.get("usage", {})
        return result

    @property
    def finish_reason(self) -> str:
        """Finish reason of the first choice."""
        if self.choices:
            result: str = self.choices[0].get("finish_reason", "")
            return result
        return ""

    @property
    def tool_calls(self) -> list[dict[str, Any]]:
        """Tool calls from the first choice's message."""
        if self.choices and self.choices[0].get("message"):
            result: list[dict[str, Any]] = self.choices[0]["message"].get("tool_calls", [])
            return result
        return []

    @property
    def has_tool_calls(self) -> bool:
        """True if the response contains tool calls."""
        return len(self.tool_calls) > 0

    @property
    def is_shear_injected(self) -> bool:
        """True if this response was injected by Shear, not from the real API."""
        return self.reason != ""


# ---------------------------------------------------------------------------
# Turn / Episode / Session
# ---------------------------------------------------------------------------


class TurnType(str, Enum):
    """Classification of a single API round-trip."""

    USER_MESSAGE = "user_message"
    TOOL_CALL_REQUEST = "tool_call_request"
    TOOL_RESULT_SUBMISSION = "tool_result_submission"
    FINAL_RESPONSE = "final_response"


@dataclass
class Turn:
    """Single request/response pair with a type annotation.

    Args:
        turn_type: Classification of this turn.
        request: The intercepted request.
        response: The intercepted response.
    """

    turn_type: TurnType
    request: InterceptedRequest
    response: InterceptedResponse


@dataclass
class Episode:
    """Group of related API calls forming one agentic task execution.

    Args:
        episode_id: Unique identifier for this episode.
        turns: Ordered list of turns in this episode.
    """

    episode_id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    turns: list[Turn] = field(default_factory=list)

    @property
    def tool_call_count(self) -> int:
        """Total tool calls across all turns in this episode."""
        return sum(t.request.tool_call_count for t in self.turns)

    @property
    def total_tokens(self) -> int:
        """Total tokens used across all turns in this episode."""
        return sum(t.response.usage.get("total_tokens", 0) for t in self.turns)


@dataclass
class Session:
    """Complete recorded session with episode structure.

    Args:
        session_id: Unique identifier for this session.
        model: Primary model used in this session.
        started_at: ISO-8601 timestamp of session start.
        episodes: Ordered list of episodes.
        metadata: Arbitrary metadata dict.
    """

    _VERSION: ClassVar[str] = "0.1.0"

    session_id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    model: str = ""
    started_at: str = ""
    episodes: list[Episode] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def total_turns(self) -> int:
        """Total number of turns across all episodes."""
        return sum(len(ep.turns) for ep in self.episodes)

    @property
    def total_tokens(self) -> int:
        """Total tokens used across all episodes."""
        return sum(ep.total_tokens for ep in self.episodes)

    def to_json(self) -> dict[str, Any]:
        """Serialize to a human-readable JSON-compatible dict.

        Returns:
            A dict suitable for ``json.dumps``.
        """
        return {
            "shear_version": self._VERSION,
            "session_id": self.session_id,
            "model": self.model,
            "started_at": self.started_at,
            "metadata": self.metadata,
            "summary": {
                "total_episodes": len(self.episodes),
                "total_turns": self.total_turns,
                "total_tokens": self.total_tokens,
            },
            "episodes": [
                {
                    "episode_id": ep.episode_id,
                    "turns": [
                        {
                            "type": turn.turn_type.value,
                            "request": {
                                "raw": turn.request.raw,
                                "timestamp": turn.request.timestamp,
                                "request_hash": turn.request.request_hash,
                            },
                            "response": {
                                "raw": turn.response.raw,
                                "status_code": turn.response.status_code,
                                "timestamp": turn.response.timestamp,
                                "latency_ms": turn.response.latency_ms,
                                "reason": turn.response.reason,
                            },
                        }
                        for turn in ep.turns
                    ],
                }
                for ep in self.episodes
            ],
        }

    @classmethod
    def from_json(cls, data: dict[str, Any]) -> Session:
        """Deserialize from a JSON-compatible dict.

        Args:
            data: A dict as produced by ``to_json``.

        Returns:
            A reconstructed Session instance.
        """
        episodes: list[Episode] = []
        for ep_data in data.get("episodes", []):
            turns: list[Turn] = []
            for turn_data in ep_data.get("turns", []):
                req_data = turn_data["request"]
                resp_data = turn_data["response"]
                req = InterceptedRequest(
                    raw=req_data["raw"],
                    timestamp=req_data.get("timestamp", 0.0),
                    request_hash=req_data.get("request_hash", ""),
                )
                resp = InterceptedResponse(
                    raw=resp_data["raw"],
                    status_code=resp_data.get("status_code", 200),
                    timestamp=resp_data.get("timestamp", 0.0),
                    latency_ms=resp_data.get("latency_ms", 0.0),
                    reason=resp_data.get("reason", ""),
                )
                turns.append(
                    Turn(
                        turn_type=TurnType(turn_data["type"]),
                        request=req,
                        response=resp,
                    )
                )
            episodes.append(
                Episode(
                    episode_id=ep_data.get("episode_id", ""),
                    turns=turns,
                )
            )
        return cls(
            session_id=data.get("session_id", ""),
            model=data.get("model", ""),
            started_at=data.get("started_at", ""),
            episodes=episodes,
            metadata=data.get("metadata", {}),
        )


# ---------------------------------------------------------------------------
# Hook control flow
# ---------------------------------------------------------------------------


class HookAction(str, Enum):
    """Possible actions a hook can return."""

    ALLOW = "allow"
    MODIFY = "modify"
    BLOCK = "block"
    SIMULATE = "simulate"


@dataclass
class HookResult:
    """Result returned by a hook to control the pipeline.

    Args:
        action: What the pipeline should do next.
        request: Modified request (for MODIFY action on before_request).
        response: Synthetic response (for SIMULATE or BLOCK actions).
        reason: Human-readable reason string.
    """

    action: HookAction
    request: InterceptedRequest | None = None
    response: InterceptedResponse | None = None
    reason: str = ""
