"""Token counting using tiktoken (optional) and provider-reported usage."""

from __future__ import annotations

from typing import Any


class TokenCounter:
    """Count tokens using tiktoken or provider-reported usage.

    Falls back gracefully if tiktoken is not installed.
    """

    def __init__(self, model: str = "") -> None:
        self._model = model
        self._encoder: Any = None
        try:
            import tiktoken  # type: ignore[import-not-found]

            self._encoder = tiktoken.encoding_for_model(model or "gpt-4o")
        except (ImportError, KeyError):
            pass

    def count(self, text: str) -> int:
        """Count tokens in a text string.

        Args:
            text: The text to count tokens for.

        Returns:
            Token count, or 0 if tiktoken is not available.
        """
        if self._encoder is not None:
            return len(self._encoder.encode(text))
        return 0

    @staticmethod
    def from_usage(usage: dict[str, int]) -> int:
        """Extract total tokens from a provider-reported usage dict.

        Args:
            usage: The usage dict from an API response.

        Returns:
            The total_tokens value, or 0 if not present.
        """
        return usage.get("total_tokens", 0)
