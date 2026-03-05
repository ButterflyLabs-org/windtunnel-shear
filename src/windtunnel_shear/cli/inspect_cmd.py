"""``shear inspect`` command — inspect a recorded session file."""

from __future__ import annotations

from pathlib import Path

import typer


def inspect_cmd(
    session_file: Path = typer.Argument(..., help="Path to the session file to inspect."),
) -> None:
    """Inspect a recorded session file.

    Displays a human-readable summary of the session including episode
    count, turn count, token usage, and model information.
    """
    typer.echo(f"Inspecting {session_file}...")
    raise NotImplementedError("Inspect command not yet implemented.")
