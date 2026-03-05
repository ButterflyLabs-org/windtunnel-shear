"""Error injection (429, 500, 503, timeout)."""

from __future__ import annotations

import time

from windtunnel_shear.core.models import InterceptedResponse

_ERROR_MESSAGES: dict[int, str] = {
    429: "Rate limit exceeded",
    500: "Internal server error",
    502: "Bad gateway",
    503: "Service unavailable",
    504: "Gateway timeout",
}


def make_error_response(status_code: int, reason: str) -> InterceptedResponse:
    """Create a synthetic error response.

    Args:
        status_code: HTTP status code to return.
        reason: Shear reason string for tracing.

    Returns:
        An InterceptedResponse representing the error.
    """
    message = _ERROR_MESSAGES.get(status_code, f"Error {status_code}")
    return InterceptedResponse(
        raw={
            "error": {
                "message": message,
                "type": "shear_fault_injection",
                "code": str(status_code),
                "source": "shear",
            }
        },
        status_code=status_code,
        timestamp=time.monotonic(),
        reason=reason,
    )
