"""OpenAI-compatible request/response parsing."""

from __future__ import annotations

import time
from typing import Any

from windtunnel_shear.core.models import InterceptedRequest, InterceptedResponse


def parse_request(body: dict[str, Any]) -> InterceptedRequest:
    """Parse a raw request body into an InterceptedRequest.

    Args:
        body: The raw JSON request body.

    Returns:
        A populated InterceptedRequest.
    """
    return InterceptedRequest(raw=body, timestamp=time.monotonic())


def parse_response(
    body: dict[str, Any], status_code: int = 200, latency_ms: float = 0.0
) -> InterceptedResponse:
    """Parse a raw response body into an InterceptedResponse.

    Args:
        body: The raw JSON response body.
        status_code: The HTTP status code.
        latency_ms: Round-trip latency in milliseconds.

    Returns:
        A populated InterceptedResponse.
    """
    return InterceptedResponse(
        raw=body,
        status_code=status_code,
        timestamp=time.monotonic(),
        latency_ms=latency_ms,
    )
