"""Jitter engine: parses --jitter CLI flags and applies prompt perturbations."""

from __future__ import annotations

import logging
from dataclasses import dataclass

from windtunnel_shear.core.models import InterceptedRequest
from windtunnel_shear.jitters.contradict import apply_contradict
from windtunnel_shear.jitters.dilute import apply_dilute
from windtunnel_shear.jitters.noise import apply_noise
from windtunnel_shear.jitters.rephrase import apply_rephrase
from windtunnel_shear.jitters.tool import get_tool_jitter_message, is_tool_jitter

logger = logging.getLogger(__name__)

_VALID_JITTER_TYPES = frozenset({
    "noise", "contradict", "dilute", "rephrase",
})


@dataclass
class JitterSpec:
    """Parsed jitter specification from a CLI flag.

    Args:
        jitter_type: One of "noise", "contradict", "dilute", "rephrase",
            or tool-* reserved.
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

    Raises:
        ValueError: If the jitter type is unknown.
    """
    parts = flag.split(":", 1)
    jitter_type = parts[0]
    params = parts[1] if len(parts) > 1 else ""

    if is_tool_jitter(jitter_type):
        logger.warning(get_tool_jitter_message())
        return JitterSpec(jitter_type=jitter_type, params=params)

    if jitter_type not in _VALID_JITTER_TYPES:
        msg = (
            f"Unknown jitter type: '{jitter_type}'. "
            f"Valid types: {', '.join(sorted(_VALID_JITTER_TYPES))}"
        )
        raise ValueError(msg)

    return JitterSpec(jitter_type=jitter_type, params=params)


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
        current = request
        for spec in self._specs:
            current = self._apply_spec(spec, current)
        return current

    def _apply_spec(
        self, spec: JitterSpec, request: InterceptedRequest,
    ) -> InterceptedRequest:
        """Apply a single jitter spec."""
        if spec.jitter_type == "noise":
            ratio = float(spec.params) if spec.params else 0.1
            return apply_noise(request, ratio)
        if spec.jitter_type == "contradict":
            return apply_contradict(request)
        if spec.jitter_type == "dilute":
            count = int(spec.params) if spec.params else 3
            return apply_dilute(request, count)
        if spec.jitter_type == "rephrase":
            return apply_rephrase(request)
        if is_tool_jitter(spec.jitter_type):
            logger.info("Skipping tool jitter '%s' (v0.1)", spec.jitter_type)
            return request
        return request
