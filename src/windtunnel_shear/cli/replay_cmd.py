"""``shear replay`` command — replay traffic from a session file."""

from __future__ import annotations

from pathlib import Path

import typer


def replay_cmd(
    input_file: Path = typer.Option(..., "-i", "--input", help="Input session file path."),
    port: int = typer.Option(9800, help="Port to listen on."),
    match_mode: str = typer.Option("sequential", help="Matching strategy: sequential or exact."),
    on_miss: str = typer.Option(
        "error", help="Cache-miss behavior: error, passthrough, or fallback."
    ),
) -> None:
    """Replay recorded responses from a session file.

    Starts a server that returns recorded responses without making real
    API calls. Useful for offline testing and CI.
    """
    typer.echo(f"Replaying from {input_file} on port {port} (mode={match_mode})...")
    raise NotImplementedError("Replay command not yet implemented.")
