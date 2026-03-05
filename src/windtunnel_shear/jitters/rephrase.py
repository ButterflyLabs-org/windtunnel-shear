"""Prompt rephrasing jitter."""

from __future__ import annotations

from windtunnel_shear.core.models import InterceptedRequest


def apply_rephrase(request: InterceptedRequest) -> InterceptedRequest:
    """Reword system prompt policies using seeded transformations.

    Args:
        request: The request to modify.

    Returns:
        The modified request with rephrased system prompt.
    """
    raise NotImplementedError
