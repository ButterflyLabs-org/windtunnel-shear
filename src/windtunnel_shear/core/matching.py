"""Replay matching strategies for recorded sessions."""

from __future__ import annotations

from abc import ABC, abstractmethod

from windtunnel_shear.core.models import (
    InterceptedRequest,
    InterceptedResponse,
    ReplayMissError,
    Session,
)


def _collect_turns(session: Session) -> list[tuple[InterceptedRequest, InterceptedResponse]]:
    """Flatten all turns from all episodes into a list."""
    turns: list[tuple[InterceptedRequest, InterceptedResponse]] = []
    for episode in session.episodes:
        for turn in episode.turns:
            turns.append((turn.request, turn.response))
    return turns


class Matcher(ABC):
    """Abstract base class for replay matching strategies."""

    @abstractmethod
    def match(self, request: InterceptedRequest) -> InterceptedResponse:
        """Find a matching recorded response for the given request.

        Args:
            request: The incoming request to match.

        Returns:
            The matching recorded response.

        Raises:
            ReplayMissError: If no match is found.
        """
        ...


class SequentialMatcher(Matcher):
    """Return recorded responses in order regardless of request content.

    Fails fast if more requests arrive than were recorded.
    """

    def __init__(self, session: Session) -> None:
        self._turns = _collect_turns(session)
        self._index = 0

    def match(self, request: InterceptedRequest) -> InterceptedResponse:
        """Return the next recorded response in sequence."""
        if self._index >= len(self._turns):
            raise ReplayMissError(
                request_hash=request.compute_hash(),
                detail=(
                    f"Sequential replay exhausted: received request "
                    f"{self._index + 1} but only {len(self._turns)} "
                    f"turns were recorded."
                ),
            )
        _, response = self._turns[self._index]
        self._index += 1
        return response


class ExactMatcher(Matcher):
    """Hash normalized request body and match against recorded hashes.

    Ignores non-deterministic fields during comparison.
    """

    def __init__(self, session: Session) -> None:
        self._index: dict[str, InterceptedResponse] = {}
        for req, resp in _collect_turns(session):
            h = req.request_hash or req.compute_hash()
            self._index[h] = resp

    def match(self, request: InterceptedRequest) -> InterceptedResponse:
        """Find a response matching the request's normalized hash."""
        request_hash = request.compute_hash()
        if request_hash in self._index:
            return self._index[request_hash]
        raise ReplayMissError(
            request_hash=request_hash,
            expected_hash=", ".join(self._index.keys()),
            detail="No recorded response matches this request hash.",
        )


def create_matcher(session: Session, mode: str = "sequential") -> Matcher:
    """Create a Matcher instance from a mode string.

    Args:
        session: The recorded session to match against.
        mode: Either "sequential" or "exact".

    Returns:
        A configured Matcher.

    Raises:
        ValueError: If the mode is unknown.
    """
    if mode == "sequential":
        return SequentialMatcher(session)
    if mode == "exact":
        return ExactMatcher(session)
    msg = f"Unknown match mode: '{mode}'. Use 'sequential' or 'exact'."
    raise ValueError(msg)
