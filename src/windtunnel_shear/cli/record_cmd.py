"""``shear record`` command — record LLM traffic to a session file."""

from __future__ import annotations

from pathlib import Path

import typer


def record_cmd(
    output: Path = typer.Option(..., "-o", "--output", help="Output session file path."),
    port: int = typer.Option(9800, help="Port to listen on."),
    upstream: str | None = typer.Option(None, help="Upstream LLM API URL."),
) -> None:
    """Record LLM API traffic to a session file.

    Starts a proxy that records all request/response pairs to the specified
    output file in Shear's self-documenting JSON format.
    """
    typer.echo(f"Recording to {output} on port {port}...")
    raise NotImplementedError("Record command not yet implemented.")
