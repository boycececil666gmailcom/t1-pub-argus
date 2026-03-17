#!/usr/bin/env python
"""
Argus — the hundred-eyed daemon.

Usage:
  python main.py start          # run daemon in foreground
  python main.py report         # today's report
  python main.py report --date 2026-03-15
  python main.py week           # this week's report
  python main.py status         # current window + idle time
  python main.py install        # add to Windows startup (registry)
  python main.py uninstall      # remove from Windows startup
"""

# region Imports

from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path

import typer
from rich.console import Console

# endregion

# region Fields / Private

app = typer.Typer(
    name="argus",
    help="Argus — always-on activity tracker and behavior reporter.",
    add_completion=False,
)
console = Console()

_STARTUP_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
_STARTUP_NAME = "ArgusDaemon"
_THIS = Path(sys.executable).resolve()
_SCRIPT = Path(__file__).resolve()

# endregion

# region Public Methods / API


@app.command()
def start() -> None:
    """Start the Argus daemon (runs in foreground; Ctrl+C to stop)."""
    from argus.daemon import run
    run()


@app.command()
def report(
    date: str = typer.Option(
        None, "--date", "-d",
        help="Date to report — YYYY-MM-DD (default: today).",
    ),
) -> None:
    """Show a daily activity report."""
    from argus.report import daily_report

    d = _parse_date(date) if date else datetime.now()
    daily_report(d)


@app.command()
def week(
    date: str = typer.Option(
        None, "--date", "-d",
        help="Any date within the desired week — YYYY-MM-DD (default: this week).",
    ),
) -> None:
    """Show a weekly activity report."""
    from argus.report import weekly_report

    d = _parse_date(date) if date else datetime.now()
    weekly_report(d)


@app.command()
def status() -> None:
    """Show what you're doing right now and your current idle time."""
    from argus.report import status_panel
    from argus.tracker import get_active_window, get_idle_seconds

    win = get_active_window()
    idle = get_idle_seconds()
    status_panel(win, idle)


@app.command()
def install() -> None:
    """Register Argus to auto-start at Windows login via the registry Run key."""
    import winreg

    value = f'"{_THIS}" "{_SCRIPT}" start'
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, _STARTUP_KEY, access=winreg.KEY_SET_VALUE)
        winreg.SetValueEx(key, _STARTUP_NAME, 0, winreg.REG_SZ, value)
        winreg.CloseKey(key)
        console.print(f"[bold green]OK[/bold green] Registered '{_STARTUP_NAME}' in startup.")
        console.print(f"   Runs: {value}")
    except OSError as e:
        console.print(f"[bold red]FAIL[/bold red] Could not write registry: {e}")
        raise typer.Exit(1)


@app.command()
def uninstall() -> None:
    """Remove the Argus auto-start registry entry."""
    import winreg

    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, _STARTUP_KEY, access=winreg.KEY_SET_VALUE)
        winreg.DeleteValue(key, _STARTUP_NAME)
        winreg.CloseKey(key)
        console.print(f"[bold green]OK[/bold green] Removed '{_STARTUP_NAME}' from startup.")
    except FileNotFoundError:
        console.print(f"[yellow]Not found[/yellow] '{_STARTUP_NAME}' was not registered.")
    except OSError as e:
        console.print(f"[bold red]FAIL[/bold red] Could not remove registry entry: {e}")
        raise typer.Exit(1)


# endregion

# region Private Methods


def _parse_date(s: str) -> datetime:
    """Parse a YYYY-MM-DD string into a datetime, exiting with an error on failure.

    Args:
        s: Date string in YYYY-MM-DD format.

    Returns:
        Parsed datetime object.

    Raises:
        typer.Exit: If the string does not match the expected format.
    """
    try:
        return datetime.strptime(s, "%Y-%m-%d")
    except ValueError:
        console.print(f"[red]Invalid date '{s}'. Use YYYY-MM-DD.[/red]")
        raise typer.Exit(1)


# endregion

if __name__ == "__main__":
    app()
