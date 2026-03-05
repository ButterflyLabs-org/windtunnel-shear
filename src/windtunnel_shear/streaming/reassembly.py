"""Collect SSE chunks into a complete response for hook processing."""

from __future__ import annotations

from collections.abc import AsyncIterator

from windtunnel_shear.core.models import InterceptedResponse


async def reassemble_stream(chunks: AsyncIterator[bytes]) -> InterceptedResponse:
    """Collect SSE chunks and build a complete InterceptedResponse.

    Args:
        chunks: Async iterator of raw SSE chunk bytes from upstream.

    Returns:
        A fully assembled InterceptedResponse.
    """
    raise NotImplementedError
