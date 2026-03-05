"""Jitter engine: parses --jitter CLI flags and applies prompt perturbations."""

from __future__ import annotations

from dataclasses import dataclass

from windtunnel_shear.core.models import InterceptedRequest


@dataclass
class JitterSpec:
    """Parsed jitter specification from a CLI flag.

    Args:
        jitter_type: One of "noise", "contradict", "dilute", "rephrase", or tool-* reserved.
        params: Optional parameter string (e.g. "0.1", "5").
    """

    jitter_type: str
    params: str = ""


def parse_jitter_flag(flag: str) -> JitterSpec:
    """Parse a --jitter flag value into a JitterSpec.

    Args:
        flag: The flag value, e.g. "noise:0.1" or "contradict".

    Returns:
        A parsed JitterSpec.
    """
    parts = flag.split(":", 1)
    return JitterSpec(jitter_type=parts[0], params=parts[1] if len(parts) > 1 else "")


class JitterEngine:
    """Applies prompt jitters to intercepted requests.

    Jitters operate on the request side (before_request) — they perturb
    prompts to test the LLM's robustness.
    """

    def __init__(self, specs: list[JitterSpec] | None = None) -> None:
        self._specs = specs or []

    def apply(self, request: InterceptedRequest) -> InterceptedRequest:
        """Apply all configured jitters to the request.

        Args:
            request: The incoming request.

        Returns:
            The (possibly modified) request with jitters applied.
        """
        raise NotImplementedError
