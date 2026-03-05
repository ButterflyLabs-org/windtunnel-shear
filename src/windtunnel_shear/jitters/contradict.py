"""Instruction contradiction jitter."""

from __future__ import annotations

from windtunnel_shear.core.models import InterceptedRequest


def apply_contradict(request: InterceptedRequest) -> InterceptedRequest:
    """Inject a contradictory user message opposing the system prompt.

    Args:
        request: The request to modify.

    Returns:
        The modified request with a contradictory instruction added.
    """
    raise NotImplementedError
