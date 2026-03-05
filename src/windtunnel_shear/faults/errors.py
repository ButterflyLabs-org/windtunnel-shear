"""Error injection (429, 500, 503, timeout)."""

from __future__ import annotations

from windtunnel_shear.core.models import InterceptedResponse


def make_error_response(status_code: int, reason: str) -> InterceptedResponse:
    """Create a synthetic error response.

    Args:
        status_code: HTTP status code to return.
        reason: Shear reason string for tracing.

    Returns:
        An InterceptedResponse representing the error.
    """
    raise NotImplementedError
