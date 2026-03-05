"""Auto-detect upstream LLM provider from the Authorization header."""

from __future__ import annotations


def detect_upstream(auth_header: str) -> str:
    """Detect the upstream API URL from an Authorization header value.

    Rules:
    - ``sk-...`` keys → ``https://api.openai.com/v1``
    - Azure deployment URLs → extracted from request
    - Falls back to empty string (caller should use ``--upstream``).

    Args:
        auth_header: The Authorization header value (e.g. "Bearer sk-...").

    Returns:
        The detected upstream base URL, or empty string if unknown.
    """
    raise NotImplementedError
