"""Fault engine: parses --fault CLI flags and applies fault injection."""

from __future__ import annotations

from dataclasses import dataclass

from windtunnel_shear.core.models import InterceptedRequest, InterceptedResponse


@dataclass
class FaultSpec:
    """Parsed fault specification from a CLI flag.

    Args:
        fault_type: One of "rate-limit", "latency", "error", "timeout".
        params: Parameter string (e.g. "0.3", "500ms", "503:0.1", "10s").
    """

    fault_type: str
    params: str


def parse_fault_flag(flag: str) -> FaultSpec:
    """Parse a --fault flag value into a FaultSpec.

    Args:
        flag: The flag value, e.g. "rate-limit:0.3" or "latency:500ms".

    Returns:
        A parsed FaultSpec.

    Raises:
        ValueError: If the flag format is invalid.
    """
    parts = flag.split(":", 1)
    if len(parts) < 2:
        raise ValueError(f"Invalid fault flag format: '{flag}'. Expected TYPE:PARAMS.")
    return FaultSpec(fault_type=parts[0], params=parts[1])


class FaultEngine:
    """Applies infrastructure faults to intercepted responses.

    Faults operate on the response side — they simulate infrastructure
    failures that test the application's resilience.
    """

    def __init__(self, specs: list[FaultSpec] | None = None) -> None:
        self._specs = specs or []

    async def maybe_inject(self, request: InterceptedRequest) -> InterceptedResponse | None:
        """Possibly inject a fault response instead of forwarding to upstream.

        Args:
            request: The incoming request.

        Returns:
            A synthetic error response if a fault fires, or None to proceed normally.
        """
        raise NotImplementedError
