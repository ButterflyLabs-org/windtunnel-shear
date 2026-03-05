"""HTTP proxy server (ASGI app powered by Starlette + uvicorn).

This is the primary transport mode: Shear runs as an HTTP proxy that
applications point at via OPENAI_BASE_URL or similar configuration.
"""

from __future__ import annotations

from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import Response
from starlette.routing import Route


async def proxy_handler(request: Request) -> Response:
    """Handle an incoming proxy request.

    Intercepts the request, runs it through the hook pipeline, forwards to
    upstream (or injects faults), and returns the response.

    Args:
        request: The incoming Starlette request.

    Returns:
        The proxied or synthetic response.
    """
    raise NotImplementedError


def create_app() -> Starlette:
    """Create the ASGI application for the proxy server.

    Returns:
        A configured Starlette application.
    """
    return Starlette(
        routes=[
            Route("/{path:path}", proxy_handler, methods=["POST", "GET", "PUT", "DELETE"]),
        ],
    )
