"""Hook registry, decorator API, and pipeline executor.

Hooks are Python functions registered via decorator that intercept and
optionally modify LLM API traffic flowing through Shear.
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from windtunnel_shear.core.models import (
    InterceptedRequest,
    InterceptedResponse,
)

logger = logging.getLogger(__name__)


@dataclass
class HookMetadata:
    """Metadata attached to a registered hook function.

    Args:
        name: Human-readable name for traces and error messages.
        category: Logical grouping (e.g. "jitter", "fault", "logging").
        stage: Ordering group — "mutate" runs before "fault" runs before "observe".
    """

    name: str
    category: str = ""
    stage: str = "default"


@dataclass
class RegisteredHook:
    """A hook function with its metadata and stage.

    Args:
        fn: The hook callable.
        metadata: Associated metadata.
        hook_type: One of "before_request", "after_response", "on_error".
    """

    fn: Callable[..., Any]
    metadata: HookMetadata
    hook_type: str


class HookRegistry:
    """Registry that stores and executes hooks in pipeline order.

    Hooks are stored as an ordered list, sorted by stage then registration
    order.  Each hook receives immutable copies (for before_request) or
    mutable references (for after_response).  Hook exceptions are caught,
    logged with full context, and optionally propagated.
    """

    def __init__(self) -> None:
        self._hooks: list[RegisteredHook] = []

    @property
    def hooks(self) -> list[RegisteredHook]:
        """Return registered hooks in execution order."""
        return list(self._hooks)

    def register(
        self,
        fn: Callable[..., Any],
        hook_type: str,
        name: str = "",
        category: str = "",
        stage: str = "default",
    ) -> None:
        """Register a hook function.

        Args:
            fn: The hook callable.
            hook_type: One of "before_request", "after_response", "on_error".
            name: Human-readable name.
            category: Logical group.
            stage: Ordering group.
        """
        meta = HookMetadata(name=name or fn.__name__, category=category, stage=stage)
        self._hooks.append(RegisteredHook(fn=fn, metadata=meta, hook_type=hook_type))

    async def run_before_request(self, request: InterceptedRequest) -> InterceptedRequest:
        """Execute all before_request hooks in order.

        Args:
            request: The incoming intercepted request.

        Returns:
            The (possibly modified) request.
        """
        raise NotImplementedError

    async def run_after_response(
        self, request: InterceptedRequest, response: InterceptedResponse
    ) -> InterceptedResponse:
        """Execute all after_response hooks in order.

        Args:
            request: The original request.
            response: The response from upstream or fault injection.

        Returns:
            The (possibly modified) response.
        """
        raise NotImplementedError

    async def run_on_error(
        self, request: InterceptedRequest, error: Exception
    ) -> InterceptedResponse | None:
        """Execute all on_error hooks in order.

        Args:
            request: The request that caused the error.
            error: The exception that occurred.

        Returns:
            An optional synthetic response, or None to propagate the error.
        """
        raise NotImplementedError


class Hook:
    """Decorator API for registering hooks.

    Example::

        @Hook.before_request(name="add_header")
        def add_header(req: InterceptedRequest) -> InterceptedRequest:
            ...
    """

    _default_registry: HookRegistry | None = None

    @classmethod
    def _get_registry(cls) -> HookRegistry:
        if cls._default_registry is None:
            cls._default_registry = HookRegistry()
        return cls._default_registry

    @classmethod
    def before_request(
        cls,
        name: str = "",
        category: str = "",
        stage: str = "default",
    ) -> Callable[..., Any]:
        """Decorator to register a before_request hook.

        Args:
            name: Human-readable name.
            category: Logical group.
            stage: Ordering group.
        """

        def decorator(fn: Callable[..., Any]) -> Callable[..., Any]:
            cls._get_registry().register(fn, "before_request", name, category, stage)
            return fn

        return decorator

    @classmethod
    def after_response(
        cls,
        name: str = "",
        category: str = "",
        stage: str = "default",
    ) -> Callable[..., Any]:
        """Decorator to register an after_response hook.

        Args:
            name: Human-readable name.
            category: Logical group.
            stage: Ordering group.
        """

        def decorator(fn: Callable[..., Any]) -> Callable[..., Any]:
            cls._get_registry().register(fn, "after_response", name, category, stage)
            return fn

        return decorator

    @classmethod
    def on_error(
        cls,
        name: str = "",
        category: str = "",
        stage: str = "default",
    ) -> Callable[..., Any]:
        """Decorator to register an on_error hook.

        Args:
            name: Human-readable name.
            category: Logical group.
            stage: Ordering group.
        """

        def decorator(fn: Callable[..., Any]) -> Callable[..., Any]:
            cls._get_registry().register(fn, "on_error", name, category, stage)
            return fn

        return decorator
