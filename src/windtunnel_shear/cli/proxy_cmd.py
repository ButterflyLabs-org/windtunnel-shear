"""``shear proxy`` command — start the HTTP proxy."""

from __future__ import annotations

from pathlib import Path

import typer


def proxy_cmd(
    port: int = typer.Option(9800, help="Port to listen on."),
    upstream: str | None = typer.Option(None, help="Upstream LLM API URL."),
    hooks: Path | None = typer.Option(None, help="Python file with hook definitions."),
    fault: list[str] | None = typer.Option(
        None, help="Fault injection spec (e.g. rate-limit:0.3)."
    ),
    jitter: list[str] | None = typer.Option(None, help="Jitter spec (e.g. noise:0.1)."),
    verbose: bool = typer.Option(False, help="Show full request/response payloads."),
    json_output: bool = typer.Option(False, "--json", help="Machine-readable JSON output."),
    quiet: bool = typer.Option(False, help="Suppress output."),
) -> None:
    """Start the Shear proxy server.

    Intercepts LLM API traffic, applies hooks/faults/jitters, and forwards
    to the upstream API. Auto-detects upstream from the Authorization header
    if --upstream is not provided.
    """
    typer.echo(f"Starting Shear proxy on port {port}...")
    raise NotImplementedError("Proxy server not yet implemented.")
