"""Re-serialize a complete response into SSE chunks for the client."""

from __future__ import annotations

from collections.abc import AsyncIterator

from windtunnel_shear.core.models import InterceptedResponse


async def restream_response(response: InterceptedResponse) -> AsyncIterator[bytes]:
    """Convert a complete response back into SSE chunks.

    Args:
        response: The complete response to re-stream.

    Yields:
        Raw SSE chunk bytes for the client.
    """
    raise NotImplementedError
    yield b""  # Make this a generator
