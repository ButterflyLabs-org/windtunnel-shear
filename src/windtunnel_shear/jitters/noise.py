"""Typo and Unicode noise injection for prompt jittering."""

from __future__ import annotations

from windtunnel_shear.core.models import InterceptedRequest


def apply_noise(request: InterceptedRequest, ratio: float) -> InterceptedRequest:
    """Inject random typos into user messages.

    Args:
        request: The request to modify.
        ratio: Fraction of characters to corrupt (0.0 to 1.0).

    Returns:
        The modified request.
    """
    raise NotImplementedError
