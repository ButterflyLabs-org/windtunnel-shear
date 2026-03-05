"""Tests for hook pipeline."""

from __future__ import annotations

import pytest

from windtunnel_shear.core.hooks import Hook, HookRegistry
from windtunnel_shear.core.models import (
    HookError,
    InterceptedRequest,
    InterceptedResponse,
)


@pytest.fixture()
def registry() -> HookRegistry:
    """A fresh HookRegistry for each test."""
    return HookRegistry()


@pytest.fixture()
def req() -> InterceptedRequest:
    return InterceptedRequest(
        raw={"model": "gpt-4o", "messages": [{"role": "user", "content": "hi"}]},
        timestamp=1.0,
    )


@pytest.fixture()
def resp() -> InterceptedResponse:
    return InterceptedResponse(
        raw={
            "choices": [
                {"message": {"role": "assistant", "content": "hello"}, "finish_reason": "stop"}
            ],
            "usage": {"prompt_tokens": 5, "completion_tokens": 3, "total_tokens": 8},
        },
        status_code=200,
    )


class TestHookRegistry:
    async def test_register_and_list(self, registry: HookRegistry) -> None:
        def my_hook(r: InterceptedRequest) -> InterceptedRequest:
            return r

        registry.register(my_hook, "before_request", name="test_hook")
        assert len(registry.hooks) == 1
        assert registry.hooks[0].metadata.name == "test_hook"

    async def test_before_request_chain(
        self, registry: HookRegistry, req: InterceptedRequest
    ) -> None:
        def add_msg(r: InterceptedRequest) -> InterceptedRequest:
            r.messages.append({"role": "system", "content": "policy"})
            return r

        def upper_content(r: InterceptedRequest) -> InterceptedRequest:
            for msg in r.messages:
                if msg.get("content"):
                    msg["content"] = msg["content"].upper()
            return r

        registry.register(add_msg, "before_request", name="add_msg")
        registry.register(upper_content, "before_request", name="upper")

        result = await registry.run_before_request(req)
        assert len(result.messages) == 2
        # upper_content ran after add_msg, so "policy" should be uppercased
        assert result.messages[1]["content"] == "POLICY"

    async def test_after_response_chain(
        self,
        registry: HookRegistry,
        req: InterceptedRequest,
        resp: InterceptedResponse,
    ) -> None:
        def append_suffix(
            _r: InterceptedRequest, response: InterceptedResponse
        ) -> InterceptedResponse:
            response.content = response.content + " [modified]"
            return response

        registry.register(append_suffix, "after_response", name="suffix")
        result = await registry.run_after_response(req, resp)
        assert result.content == "hello [modified]"

    async def test_on_error_returns_response(
        self, registry: HookRegistry, req: InterceptedRequest
    ) -> None:
        def handle_error(_r: InterceptedRequest, _err: Exception) -> InterceptedResponse:
            return InterceptedResponse(
                raw={"choices": [{"message": {"content": "fallback"}, "finish_reason": "stop"}]},
                status_code=200,
                reason="error_handler",
            )

        registry.register(handle_error, "on_error", name="handler")
        result = await registry.run_on_error(req, RuntimeError("boom"))
        assert result is not None
        assert result.content == "fallback"
        assert result.is_shear_injected

    async def test_on_error_returns_none(
        self, registry: HookRegistry, req: InterceptedRequest
    ) -> None:
        def ignore_error(_r: InterceptedRequest, _err: Exception) -> None:
            return None

        registry.register(ignore_error, "on_error", name="ignore")
        result = await registry.run_on_error(req, RuntimeError("boom"))
        assert result is None

    async def test_hook_exception_propagates(
        self, registry: HookRegistry, req: InterceptedRequest
    ) -> None:
        def bad_hook(_r: InterceptedRequest) -> InterceptedRequest:
            msg = "intentional"
            raise ValueError(msg)

        registry.register(bad_hook, "before_request", name="bad_hook")
        with pytest.raises(HookError) as exc_info:
            await registry.run_before_request(req)
        assert "bad_hook" in str(exc_info.value)
        assert isinstance(exc_info.value.original, ValueError)

    async def test_hook_exception_suppressed(self, req: InterceptedRequest) -> None:
        registry = HookRegistry(propagate_errors=False)

        def bad_hook(_r: InterceptedRequest) -> InterceptedRequest:
            msg = "intentional"
            raise ValueError(msg)

        registry.register(bad_hook, "before_request", name="bad_hook")
        # Should not raise — error is suppressed
        result = await registry.run_before_request(req)
        assert result is req  # returns original since hook returned None

    async def test_stage_ordering(self, registry: HookRegistry, req: InterceptedRequest) -> None:
        execution_order: list[str] = []

        def observe_hook(r: InterceptedRequest) -> InterceptedRequest:
            execution_order.append("observe")
            return r

        def mutate_hook(r: InterceptedRequest) -> InterceptedRequest:
            execution_order.append("mutate")
            return r

        def default_hook(r: InterceptedRequest) -> InterceptedRequest:
            execution_order.append("default")
            return r

        # Register in reverse order — should still execute in stage order
        registry.register(observe_hook, "before_request", name="obs", stage="observe")
        registry.register(default_hook, "before_request", name="def", stage="default")
        registry.register(mutate_hook, "before_request", name="mut", stage="mutate")

        await registry.run_before_request(req)
        assert execution_order == ["mutate", "default", "observe"]

    async def test_async_hook(self, registry: HookRegistry, req: InterceptedRequest) -> None:
        async def async_hook(r: InterceptedRequest) -> InterceptedRequest:
            r.messages.append({"role": "system", "content": "async"})
            return r

        registry.register(async_hook, "before_request", name="async_hook")
        result = await registry.run_before_request(req)
        assert any(m["content"] == "async" for m in result.messages)

    async def test_hook_skips_non_matching_type(
        self, registry: HookRegistry, req: InterceptedRequest
    ) -> None:
        called = False

        def after_hook(_r: InterceptedRequest, _resp: InterceptedResponse) -> InterceptedResponse:
            nonlocal called
            called = True
            return _resp

        registry.register(after_hook, "after_response", name="after_hook")
        # run_before_request should not call after_response hooks
        await registry.run_before_request(req)
        assert not called

    async def test_empty_registry(
        self, registry: HookRegistry, req: InterceptedRequest, resp: InterceptedResponse
    ) -> None:
        # All methods should work with no hooks registered
        result_req = await registry.run_before_request(req)
        assert result_req is req
        result_resp = await registry.run_after_response(req, resp)
        assert result_resp is resp
        result_err = await registry.run_on_error(req, RuntimeError("test"))
        assert result_err is None


class TestHookDecorator:
    def setup_method(self) -> None:
        Hook._reset_registry()

    def teardown_method(self) -> None:
        Hook._reset_registry()

    def test_before_request_decorator(self) -> None:
        @Hook.before_request(name="test_br")
        def my_hook(req: InterceptedRequest) -> InterceptedRequest:
            return req

        registry = Hook._get_registry()
        assert len(registry.hooks) == 1
        assert registry.hooks[0].hook_type == "before_request"
        assert registry.hooks[0].metadata.name == "test_br"

    def test_after_response_decorator(self) -> None:
        @Hook.after_response(name="test_ar", category="logging")
        def my_hook(_req: InterceptedRequest, resp: InterceptedResponse) -> InterceptedResponse:
            return resp

        registry = Hook._get_registry()
        assert len(registry.hooks) == 1
        assert registry.hooks[0].metadata.category == "logging"

    def test_on_error_decorator(self) -> None:
        @Hook.on_error(name="test_err")
        def my_hook(_req: InterceptedRequest, _err: Exception) -> None:
            return None

        registry = Hook._get_registry()
        assert len(registry.hooks) == 1
        assert registry.hooks[0].hook_type == "on_error"

    def test_decorator_preserves_function(self) -> None:
        @Hook.before_request(name="test")
        def my_hook(req: InterceptedRequest) -> InterceptedRequest:
            return req

        assert callable(my_hook)
        assert my_hook.__name__ == "my_hook"

    def test_default_name_from_function(self) -> None:
        @Hook.before_request()
        def my_custom_hook(req: InterceptedRequest) -> InterceptedRequest:
            return req

        registry = Hook._get_registry()
        assert registry.hooks[0].metadata.name == "my_custom_hook"
