"""Typo and Unicode noise injection for prompt jittering."""

from __future__ import annotations

import random
import string

from windtunnel_shear.core.models import InterceptedRequest

_TYPO_MAP: dict[str, str] = {
    "a": "s", "b": "v", "c": "x", "d": "f", "e": "r",
    "f": "g", "g": "h", "h": "j", "i": "o", "j": "k",
    "k": "l", "l": ";", "m": "n", "n": "b", "o": "p",
    "p": "o", "q": "w", "r": "t", "s": "d", "t": "y",
    "u": "i", "v": "c", "w": "e", "x": "z", "y": "u",
    "z": "x",
}


def _corrupt_char(c: str, rng: random.Random) -> str:
    """Corrupt a single character using keyboard-adjacent substitution."""
    lower = c.lower()
    if lower in _TYPO_MAP:
        replacement = _TYPO_MAP[lower]
        return replacement.upper() if c.isupper() else replacement
    if c.isdigit():
        return rng.choice(string.digits)
    return c


def _inject_noise(text: str, ratio: float, rng: random.Random) -> str:
    """Inject typos into text at the given ratio."""
    if ratio <= 0 or not text:
        return text
    chars = list(text)
    for i in range(len(chars)):
        if chars[i].isalnum() and rng.random() < ratio:
            chars[i] = _corrupt_char(chars[i], rng)
    return "".join(chars)


def apply_noise(
    request: InterceptedRequest, ratio: float, *, seed: int | None = None,
) -> InterceptedRequest:
    """Inject random typos into user messages.

    Args:
        request: The request to modify.
        ratio: Fraction of characters to corrupt (0.0 to 1.0).
        seed: Optional random seed for reproducibility.

    Returns:
        The modified request.
    """
    rng = random.Random(seed)
    for msg in request.messages:
        if msg.get("role") == "user" and isinstance(msg.get("content"), str):
            msg["content"] = _inject_noise(msg["content"], ratio, rng)
    return request
