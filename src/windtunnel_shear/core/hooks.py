"""Hook registry, decorator API, and pipeline executor.

Hooks are Python functions registered via decorator that intercept and
optionally modify LLM API traffic flowing through Shear.
"""

from __future__ import annotations

import asyncio
import inspect
import logging
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from windtunnel_shear.core.models import (
    HookError,
    InterceptedRequest,
    InterceptedResponse,
)

logger = logging.getLogger(__name__)

# Stage ordering — earlier stages run first.
_STAGE_ORDER: dict[str, int] = {
    "mutate": 0,
    "fault": 1,
    "default": 2,
    "observe": 3,
}


def _stage_sort_key(hook: RegisteredHook) -> tuple[int, int]:
    """Sort key: (stage_priority, registration_order)."""
    return (_STAGE_ORDER.get(hook.metadata.stage, 2), hook._order)


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
    _order: int = 0


class HookRegistry:
    """Registry that stores and executes hooks in pipeline order.

    Hooks are stored as an ordered list, sorted by stage then registration
    order.  Hook exceptions are caught, logged with full context (hook name,
    source file, line), and re-raised as HookError.
    """

    def __init__(self, *, propagate_errors: bool = True) -> None:
        self._hooks: list[RegisteredHook] = []
        self._counter: int = 0
        self._propagate_errors = propagate_errors

    @property
    def hooks(self) -> list[RegisteredHook]:
        """Return registered hooks in execution order."""
        return sorted(self._hooks, key=_stage_sort_key)

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
        self._hooks.append(
            RegisteredHook(fn=fn, metadata=meta, hook_type=hook_type, _order=self._counter)
        )
        self._counter += 1

    def _get_source_info(self, fn: Callable[..., Any]) -> tuple[str, int]:
        """Extract source file and line from a callable."""
        try:
            source_file = inspect.getfile(fn)
            _, line_no = inspect.getsourcelines(fn)
            return source_file, line_no
        except (TypeError, OSError):
            return "", 0

    async def _call_hook(self, hook: RegisteredHook, *args: Any) -> Any:
        """Call a hook function, handling both sync and async hooks.

        Args:
            hook: The registered hook to call.
            *args: Arguments to pass to the hook.

        Returns:
            The hook's return value.

        Raises:
            HookError: If the hook raises an exception and propagation is enabled.
        """
        try:
            result = hook.fn(*args)
            if asyncio.iscoroutine(result):
                result = await result
            return result
        except HookError:
            raise
        except Exception as exc:
            source_file, line = self._get_source_info(hook.fn)
            hook_error = HookError(
                hook_name=hook.metadata.name,
                original=exc,
                source_file=source_file,
                line=line,
            )
            logger.error("%s", hook_error)
            if self._propagate_errors:
                raise hook_error from exc
            return None

    async def run_before_request(self, request: InterceptedRequest) -> InterceptedRequest:
        """Execute all before_request hooks in order.

        Each hook receives the request and must return a (possibly modified)
        request. Hooks chain — the output of one is the input to the next.

        Args:
            request: The incoming intercepted request.

        Returns:
            The (possibly modified) request.
        """
        current = request
        for hook in self.hooks:
            if hook.hook_type != "before_request":
                continue
            result = await self._call_hook(hook, current)
            if isinstance(result, InterceptedRequest):
                current = result
        return current

    async def run_after_response(
        self, request: InterceptedRequest, response: InterceptedResponse
    ) -> InterceptedResponse:
        """Execute all after_response hooks in order.

        Each hook receives the original request and the response, and must
        return a (possibly modified) response.

        Args:
            request: The original request.
            response: The response from upstream or fault injection.

        Returns:
            The (possibly modified) response.
        """
        current = response
        for hook in self.hooks:
            if hook.hook_type != "after_response":
                continue
            result = await self._call_hook(hook, request, current)
            if isinstance(result, InterceptedResponse):
                current = result
        return current

    async def run_on_error(
        self, request: InterceptedRequest, error: Exception
    ) -> InterceptedResponse | None:
        """Execute all on_error hooks in order.

        Each hook receives the request and the error. If a hook returns an
        InterceptedResponse, it becomes the response (error is swallowed).
        If all hooks return None, the error propagates.

        Args:
            request: The request that caused the error.
            error: The exception that occurred.

        Returns:
            An optional synthetic response, or None to propagate the error.
        """
        for hook in self.hooks:
            if hook.hook_type != "on_error":
                continue
            result = await self._call_hook(hook, request, error)
            if isinstance(result, InterceptedResponse):
                return result
        return None


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
    def _reset_registry(cls) -> None:
        """Reset the default registry. Used in tests."""
        cls._default_registry = None

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
