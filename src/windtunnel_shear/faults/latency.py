"""Latency injection for simulating slow upstream responses."""

from __future__ import annotations

import asyncio


async def inject_latency(duration_ms: float) -> None:
    """Sleep for the specified duration to simulate latency.

    Args:
        duration_ms: Delay in milliseconds.
    """
    if duration_ms > 0:
        await asyncio.sleep(duration_ms / 1000.0)


def parse_duration(value: str) -> float:
    """Parse a duration string into milliseconds.

    Supports formats: "500ms", "1.5s", "500" (interpreted as ms).

    Args:
        value: Duration string.

    Returns:
        Duration in milliseconds.

    Raises:
        ValueError: If the format is unrecognized.
    """
    value = value.strip()
    if value.endswith("ms"):
        return float(value[:-2])
    if value.endswith("s"):
        return float(value[:-1]) * 1000
    return float(value)
