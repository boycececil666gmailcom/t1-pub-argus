#!/usr/bin/env python
"""
Argus — the hundred-eyed daemon.

Usage:
  python main.py start          # run daemon in foreground
  python main.py tui            # interactive TUI dashboard
  python main.py report         # today's activity report
  python main.py report --date 2026-03-15
  python main.py week           # this week's report
  python main.py status         # current window + idle time
  python main.py install        # register daemon to run at login
  python main.py uninstall      # remove from auto-start

Platform support:
  Windows  — registry Run key          (no extra tools needed)
  macOS    — LaunchAgent plist         (no extra tools needed)
  Linux    — XDG autostart .desktop    (no extra tools needed)
             Tracking requires: sudo apt install xdotool xprintidle
"""

# region Imports

from __future__ import annotations

from datetime import datetime

import typer
from rich.console import Console

# endregion

# region Setup

app = typer.Typer(
    name="argus",
    help="Argus — always-on activity tracker and behaviour reporter.",
    add_completion=False,
    invoke_without_command=True,  # allows the callback below to run with no subcommand
)
console = Console()

# endregion

# region Commands


@app.callback()
def _default(ctx: typer.Context) -> None:
    """Launch the TUI dashboard when Argus is run with no subcommand.

    This means double-clicking argus.exe opens the dashboard directly
    instead of showing a 'Missing command' error and closing immediately.
    """
    if ctx.invoked_subcommand is None:
        from argus.tui import run
        run()


@app.command()
def start() -> None:
    """Start the Argus daemon (runs in foreground; Ctrl+C to stop)."""
    from argus.daemon import run
    run()


@app.command()
def tui() -> None:
    """Launch the interactive Textual TUI dashboard."""
    from argus.tui import run
    run()



@app.command()
def report(
    date: str = typer.Option(
        None, "--date", "-d",
        help="Date to report — YYYY-MM-DD (default: today).",
    ),
) -> None:
    """Show a daily activity report (also saves plain text under your Argus data folder)."""
    from argus.report import daily_report
    daily_report(_parse_date(date) if date else datetime.now())


@app.command()
def week(
    date: str = typer.Option(
        None, "--date", "-d",
        help="Any date within the desired week — YYYY-MM-DD (default: this week).",
    ),
) -> None:
    """Show a weekly activity report (also saves plain text under your Argus data folder)."""
    from argus.report import weekly_report
    weekly_report(_parse_date(date) if date else datetime.now())


@app.command()
def status() -> None:
    """Show what you are doing right now and your current idle time."""
    from argus.report import status_panel
    from argus.tracker import get_active_window, get_idle_seconds
    status_panel(get_active_window(), get_idle_seconds())


@app.command()
def install() -> None:
    """Register Argus to start automatically at login."""
    from argus.autostart import enable, is_enabled
    if is_enabled():
        console.print("[yellow]Already registered.[/yellow] Argus is already set to auto-start.")
        return
    try:
        enable()
        console.print("[bold green]OK[/bold green] Argus will start automatically at login.")
    except Exception as exc:
        console.print(f"[bold red]FAIL[/bold red] {exc}")
        raise typer.Exit(1)


@app.command()
def uninstall() -> None:
    """Remove Argus from the login auto-start list."""
    from argus.autostart import disable, is_enabled
    if not is_enabled():
        console.print("[yellow]Not registered.[/yellow] Argus was not set to auto-start.")
        return
    try:
        disable()
        console.print("[bold green]OK[/bold green] Argus removed from auto-start.")
    except Exception as exc:
        console.print(f"[bold red]FAIL[/bold red] {exc}")
        raise typer.Exit(1)


# endregion

# region Helpers


def _parse_date(s: str) -> datetime:
    """Parse a YYYY-MM-DD string, printing a friendly error and exiting on failure."""
    try:
        return datetime.strptime(s, "%Y-%m-%d")
    except ValueError:
        console.print(f"[red]Invalid date '{s}'. Use YYYY-MM-DD.[/red]")
        raise typer.Exit(1)


# endregion

if __name__ == "__main__":
    app()
