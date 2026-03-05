"""Typer app and top-level command routing for the ``shear`` CLI."""

from __future__ import annotations

import typer

from windtunnel_shear.cli.inspect_cmd import inspect_cmd
from windtunnel_shear.cli.proxy_cmd import proxy_cmd
from windtunnel_shear.cli.record_cmd import record_cmd
from windtunnel_shear.cli.replay_cmd import replay_cmd
from windtunnel_shear.cli.simulate_cmd import simulate_cmd

app = typer.Typer(
    name="shear",
    help="Wind shear for LLM APIs — intercept, mutate, record, replay, and stress-test.",
    no_args_is_help=True,
    add_completion=False,
)

app.command("proxy")(proxy_cmd)
app.command("record")(record_cmd)
app.command("replay")(replay_cmd)
app.command("simulate")(simulate_cmd)
app.command("inspect")(inspect_cmd)


if __name__ == "__main__":
    app()
