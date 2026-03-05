"""Tool jitter stubs — reserved namespace for v0.1.

These jitter types are parsed from CLI flags but return a helpful message
indicating they will ship in v0.1.
"""

from __future__ import annotations

_TOOL_JITTER_MESSAGE = (
    "Tool jitters (tool-corrupt, tool-drop, tool-fail, tool-delay) "
    "are reserved for v0.1. See the roadmap for details."
)

RESERVED_TOOL_JITTERS = frozenset(
    {
        "tool-corrupt",
        "tool-drop",
        "tool-fail",
        "tool-delay",
    }
)


def is_tool_jitter(jitter_type: str) -> bool:
    """Check if a jitter type is a reserved tool jitter.

    Args:
        jitter_type: The jitter type string to check.

    Returns:
        True if this is a reserved tool jitter type.
    """
    return jitter_type in RESERVED_TOOL_JITTERS


def get_tool_jitter_message() -> str:
    """Return the helpful message for reserved tool jitters.

    Returns:
        A string explaining that tool jitters ship in v0.1.
    """
    return _TOOL_JITTER_MESSAGE
