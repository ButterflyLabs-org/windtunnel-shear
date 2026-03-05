"""``shear simulate`` command — serve synthetic responses from fixture files."""

from __future__ import annotations

from pathlib import Path

import typer


def simulate_cmd(
    responses: Path = typer.Option(..., help="JSON file with synthetic responses."),
    port: int = typer.Option(9800, help="Port to listen on."),
) -> None:
    """Serve synthetic responses from a fixture file.

    Useful for testing without any upstream API — responses are served
    directly from the provided JSON file.
    """
    typer.echo(f"Simulating from {responses} on port {port}...")
    raise NotImplementedError("Simulate command not yet implemented.")
