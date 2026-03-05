"""Context dilution jitter."""

from __future__ import annotations

from windtunnel_shear.core.models import InterceptedRequest


def apply_dilute(request: InterceptedRequest, count: int) -> InterceptedRequest:
    """Pad the conversation with irrelevant turns.

    Args:
        request: The request to modify.
        count: Number of irrelevant turn pairs to insert.

    Returns:
        The modified request with diluted context.
    """
    raise NotImplementedError
