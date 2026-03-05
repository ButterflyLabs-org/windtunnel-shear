"""Latency injection for simulating slow upstream responses."""

from __future__ import annotations


async def inject_latency(duration_ms: float) -> None:
    """Sleep for the specified duration to simulate latency.

    Args:
        duration_ms: Delay in milliseconds.
    """
    raise NotImplementedError
