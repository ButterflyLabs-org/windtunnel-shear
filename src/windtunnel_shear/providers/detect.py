"""Auto-detect upstream LLM provider from the Authorization header."""

from __future__ import annotations


def detect_upstream(auth_header: str) -> str:
    """Detect the upstream API URL from an Authorization header value.

    Rules:
    - ``sk-ant-...`` keys → ``https://api.anthropic.com/v1``
    - ``sk-...`` keys → ``https://api.openai.com/v1``
    - Falls back to empty string (caller should use ``--upstream``).

    Args:
        auth_header: The Authorization header value (e.g. "Bearer sk-...").

    Returns:
        The detected upstream base URL, or empty string if unknown.
    """
    # Strip "Bearer " prefix if present
    token = auth_header.strip()
    if token.lower().startswith("bearer "):
        token = token[7:]
    token = token.strip()

    if not token:
        return ""

    # Anthropic keys: sk-ant-...
    if token.startswith("sk-ant-"):
        return "https://api.anthropic.com/v1"

    # OpenAI keys: sk-... (but not sk-ant-)
    if token.startswith("sk-"):
        return "https://api.openai.com/v1"

    return ""
