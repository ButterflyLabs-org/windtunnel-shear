"""windtunnel-shear — intercept, mutate, record, replay, and stress-test LLM conversations.

Public API:

- ``wrap(client)``: Wrap an LLM client for library-mode interception.
- ``Hook``: Decorator API for registering hooks.
- ``InterceptedRequest``, ``InterceptedResponse``: Core data models.
"""

from __future__ import annotations

from windtunnel_shear.core.hooks import Hook
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
from windtunnel_shear.transport.library import wrap

__all__ = [
    "Episode",
    "FaultInjectedError",
    "Hook",
    "HookAction",
    "HookError",
    "HookResult",
    "InterceptedRequest",
    "InterceptedResponse",
    "ReplayMissError",
    "Session",
    "ShearError",
    "Turn",
    "TurnType",
    "UpstreamError",
    "wrap",
]
