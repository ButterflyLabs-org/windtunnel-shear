"""Session recorder and episode grouping logic."""

from __future__ import annotations

from windtunnel_shear.core.models import Episode, InterceptedRequest, InterceptedResponse, Session


class SessionRecorder:
    """Records intercepted traffic into a Session with episode grouping.

    The recorder accumulates turns and groups them into episodes based on
    conversation boundaries (e.g. a new user message after a final response).
    """

    def __init__(self) -> None:
        self._session = Session()
        self._current_episode: Episode | None = None

    @property
    def session(self) -> Session:
        """Return the current session being recorded."""
        return self._session

    def record_turn(self, request: InterceptedRequest, response: InterceptedResponse) -> None:
        """Record a single request/response turn.

        Args:
            request: The intercepted request.
            response: The intercepted response.
        """
        raise NotImplementedError

    def finalize(self) -> Session:
        """Finalize and return the completed session.

        Returns:
            The recorded session with all episodes closed.
        """
        raise NotImplementedError
