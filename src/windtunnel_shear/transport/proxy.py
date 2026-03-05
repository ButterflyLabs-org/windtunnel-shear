"""HTTP proxy server (ASGI app powered by Starlette + uvicorn).

This is the primary transport mode: Shear runs as an HTTP proxy that
applications point at via OPENAI_BASE_URL or similar configuration.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from typing import Any

import httpx
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.routing import Route

from windtunnel_shear.cli.formatter import log_exchange
from windtunnel_shear.core.hooks import HookRegistry
from windtunnel_shear.core.models import InterceptedRequest, InterceptedResponse
from windtunnel_shear.providers.detect import detect_upstream

logger = logging.getLogger(__name__)


@dataclass
class ProxyConfig:
    """Configuration for the proxy server.

    Args:
        upstream: Explicit upstream URL, or empty to auto-detect.
        verbose: Show full request/response payloads.
        json_output: Machine-readable JSON output.
        quiet: Suppress console output.
    """

    upstream: str = ""
    verbose: bool = False
    json_output: bool = False
    quiet: bool = False
    hook_registry: HookRegistry = field(default_factory=HookRegistry)


# Module-level config — set before starting the server.
_config = ProxyConfig()
_http_client: httpx.AsyncClient | None = None


def _get_client() -> httpx.AsyncClient:
    """Get or create the shared async HTTP client."""
    global _http_client
    if _http_client is None:
        _http_client = httpx.AsyncClient(timeout=httpx.Timeout(120.0))
    return _http_client


def _resolve_upstream(request: Request) -> str:
    """Determine the upstream URL for a request.

    Uses explicit config if set, otherwise auto-detects from the
    Authorization header.

    Args:
        request: The incoming Starlette request.

    Returns:
        The upstream base URL.

    Raises:
        ValueError: If no upstream can be determined.
    """
    if _config.upstream:
        return _config.upstream

    auth_header = request.headers.get("authorization", "")
    detected = detect_upstream(auth_header)
    if detected:
        return detected

    msg = (
        "Could not auto-detect upstream. Either set --upstream explicitly "
        "or use a recognized API key format (sk-... for OpenAI)."
    )
    raise ValueError(msg)


async def proxy_handler(request: Request) -> Response:
    """Handle an incoming proxy request.

    Intercepts the request, runs it through the hook pipeline, forwards to
    upstream, and returns the response.

    Args:
        request: The incoming Starlette request.

    Returns:
        The proxied or synthetic response.
    """
    # Parse request body
    try:
        body = await request.json()
    except Exception:
        return JSONResponse(
            {"error": {"message": "Invalid JSON in request body", "source": "shear"}},
            status_code=400,
        )

    # Build InterceptedRequest
    intercepted_req = InterceptedRequest(raw=body, timestamp=time.monotonic())

    # Run before_request hooks
    try:
        intercepted_req = await _config.hook_registry.run_before_request(intercepted_req)
    except Exception as exc:
        return JSONResponse(
            {
                "error": {
                    "message": f"Hook error: {exc}",
                    "source": "shear",
                }
            },
            status_code=500,
        )

    # Resolve upstream
    try:
        upstream = _resolve_upstream(request)
    except ValueError as exc:
        return JSONResponse(
            {"error": {"message": str(exc), "source": "shear"}},
            status_code=502,
        )

    # Build upstream URL
    path = request.path_params.get("path", "")
    upstream_url = f"{upstream.rstrip('/')}/{path}" if path else upstream

    # Forward headers (pass through auth, content-type, etc.)
    forward_headers: dict[str, str] = {}
    for key in ("authorization", "content-type", "accept"):
        val = request.headers.get(key)
        if val:
            forward_headers[key] = val

    # Forward to upstream
    start_time = time.monotonic()
    try:
        client = _get_client()
        upstream_resp = await client.post(
            upstream_url,
            json=intercepted_req.raw,
            headers=forward_headers,
        )
        latency_ms = (time.monotonic() - start_time) * 1000

        resp_body: dict[str, Any] = upstream_resp.json()
        intercepted_resp = InterceptedResponse(
            raw=resp_body,
            status_code=upstream_resp.status_code,
            timestamp=time.monotonic(),
            latency_ms=latency_ms,
        )
    except httpx.TimeoutException:
        intercepted_resp = InterceptedResponse(
            raw={"error": {"message": "Upstream request timed out", "source": "shear"}},
            status_code=504,
            timestamp=time.monotonic(),
            latency_ms=(time.monotonic() - start_time) * 1000,
            reason="shear:timeout",
        )
    except Exception as exc:
        # Try on_error hooks
        error_resp = await _config.hook_registry.run_on_error(intercepted_req, exc)
        if error_resp is not None:
            intercepted_resp = error_resp
        else:
            intercepted_resp = InterceptedResponse(
                raw={
                    "error": {
                        "message": f"Upstream connection error: {exc}",
                        "source": "shear",
                    }
                },
                status_code=502,
                timestamp=time.monotonic(),
                latency_ms=(time.monotonic() - start_time) * 1000,
                reason="shear:connection_error",
            )

    # Run after_response hooks
    try:
        intercepted_resp = await _config.hook_registry.run_after_response(
            intercepted_req, intercepted_resp
        )
    except Exception as exc:
        logger.error("after_response hook error: %s", exc)

    # Log the exchange
    log_exchange(
        intercepted_req,
        intercepted_resp,
        verbose=_config.verbose,
        json_mode=_config.json_output,
        quiet=_config.quiet,
    )

    return JSONResponse(intercepted_resp.raw, status_code=intercepted_resp.status_code)


async def _on_shutdown() -> None:
    """Clean up resources on server shutdown."""
    global _http_client
    if _http_client is not None:
        await _http_client.aclose()
        _http_client = None


def create_app(config: ProxyConfig | None = None) -> Starlette:
    """Create the ASGI application for the proxy server.

    Args:
        config: Optional proxy configuration. Uses module-level default if not provided.

    Returns:
        A configured Starlette application.
    """
    global _config
    if config is not None:
        _config = config

    return Starlette(
        routes=[
            Route("/{path:path}", proxy_handler, methods=["POST", "GET", "PUT", "DELETE"]),
        ],
        on_shutdown=[_on_shutdown],
    )
