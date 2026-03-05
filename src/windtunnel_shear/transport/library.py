"""Library mode wrapper — the wrap() function.

Provides one-line integration for wrapping an existing LLM client
(e.g. OpenAI) so that all calls flow through Shear's hook pipeline.
"""

from __future__ import annotations

from typing import Any


def wrap(client: Any) -> Any:
    """Wrap an LLM client so its calls flow through Shear.

    Example::

        from windtunnel_shear import wrap
        from openai import OpenAI

        client = wrap(OpenAI())

    Args:
        client: An LLM client instance (e.g. ``openai.OpenAI``).

    Returns:
        A wrapped client that intercepts all API calls.
    """
    raise NotImplementedError
