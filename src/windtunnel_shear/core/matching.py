"""Replay matching strategies for recorded sessions."""

from __future__ import annotations

from abc import ABC, abstractmethod

from windtunnel_shear.core.models import InterceptedRequest, InterceptedResponse, Session


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
        self._session = session
        self._index = 0

    def match(self, request: InterceptedRequest) -> InterceptedResponse:
        """Return the next recorded response in sequence.

        Args:
            request: The incoming request (ignored for matching).

        Returns:
            The next recorded response.

        Raises:
            ReplayMissError: If all recorded responses have been consumed.
        """
        raise NotImplementedError


class ExactMatcher(Matcher):
    """Hash normalized request body and match against recorded hashes.

    Ignores non-deterministic fields during comparison.
    """

    def __init__(self, session: Session) -> None:
        self._session = session
        self._index: dict[str, InterceptedResponse] = {}

    def match(self, request: InterceptedRequest) -> InterceptedResponse:
        """Find a response matching the request's normalized hash.

        Args:
            request: The incoming request to match by hash.

        Returns:
            The matching recorded response.

        Raises:
            ReplayMissError: If no recorded response matches the hash.
        """
        raise NotImplementedError
