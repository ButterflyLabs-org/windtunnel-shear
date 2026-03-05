"""OpenAI-compatible request/response parsing."""

from __future__ import annotations

from typing import Any

from windtunnel_shear.core.models import InterceptedRequest, InterceptedResponse


def parse_request(body: dict[str, Any]) -> InterceptedRequest:
    """Parse a raw request body into an InterceptedRequest.

    Args:
        body: The raw JSON request body.

    Returns:
        A populated InterceptedRequest.
    """
    raise NotImplementedError


def parse_response(body: dict[str, Any], status_code: int = 200) -> InterceptedResponse:
    """Parse a raw response body into an InterceptedResponse.

    Args:
        body: The raw JSON response body.
        status_code: The HTTP status code.

    Returns:
        A populated InterceptedResponse.
    """
    raise NotImplementedError
