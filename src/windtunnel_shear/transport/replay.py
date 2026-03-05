"""Replay server — serves responses from recorded session files."""

from __future__ import annotations

from windtunnel_shear.core.models import Session


class ReplayServer:
    """Serves recorded responses from a session file.

    Can operate in sequential or exact matching mode, with configurable
    cache-miss behavior.
    """

    def __init__(
        self,
        session: Session,
        match_mode: str = "sequential",
        on_miss: str = "error",
    ) -> None:
        self._session = session
        self._match_mode = match_mode
        self._on_miss = on_miss

    async def start(self, port: int = 9800) -> None:
        """Start the replay server.

        Args:
            port: Port to listen on.
        """
        raise NotImplementedError
