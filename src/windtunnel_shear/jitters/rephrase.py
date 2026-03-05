"""Prompt rephrasing jitter."""

from __future__ import annotations

import re

from windtunnel_shear.core.models import InterceptedRequest

_SUBSTITUTIONS: list[tuple[str, str]] = [
    ("must", "should"),
    ("always", "typically"),
    ("never", "rarely"),
    ("ensure", "try to"),
    ("required", "recommended"),
    ("shall", "may"),
    ("forbidden", "discouraged"),
    ("mandatory", "suggested"),
    ("do not", "avoid"),
    ("critical", "important"),
]


def _rephrase_text(text: str) -> str:
    """Apply deterministic word substitutions to rephrase text."""
    result = text
    for original, replacement in _SUBSTITUTIONS:
        pattern = re.compile(re.escape(original), re.IGNORECASE)
        repl: str = replacement

        def _sub(m: re.Match[str], r: str = repl) -> str:
            return r.capitalize() if m.group()[0].isupper() else r

        result = pattern.sub(_sub, result)
    return result


def apply_rephrase(request: InterceptedRequest) -> InterceptedRequest:
    """Reword system prompt policies using seeded transformations.

    Applies deterministic word substitutions to system messages to test
    whether the LLM's behavior changes with slightly different phrasing.

    Args:
        request: The request to modify.

    Returns:
        The modified request with rephrased system prompt.
    """
    for msg in request.messages:
        if msg.get("role") == "system" and isinstance(msg.get("content"), str):
            msg["content"] = _rephrase_text(msg["content"])
    return request
