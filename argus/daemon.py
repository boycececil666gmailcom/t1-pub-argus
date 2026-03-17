"""The always-on polling daemon."""

# region Imports

import signal
import time

from rich.console import Console

from .config import IDLE_THRESHOLD, POLL_INTERVAL
from .storage import init_db, record
from .tracker import get_active_window, get_idle_seconds

# endregion

# region Fields / Private

console = Console()
_running = True

# endregion

# region Private Methods


def _handle_signal(sig, frame):  # noqa: ARG001
    """Gracefully stop the daemon loop on SIGINT or SIGTERM."""
    global _running
    _running = False


# endregion

# region Public Methods / API


def run() -> None:
    """Start the Argus polling loop.

    Initialises the database, registers signal handlers, then polls the active
    window every POLL_INTERVAL seconds until interrupted. Each snapshot is
    written to the database with an idle flag when the user has been inactive
    for longer than IDLE_THRESHOLD seconds.
    """
    init_db()

    signal.signal(signal.SIGINT, _handle_signal)
    signal.signal(signal.SIGTERM, _handle_signal)

    console.rule("[bold cyan]Argus[/bold cyan]")
    console.print(
        f"  Daemon started  ·  poll every [bold]{POLL_INTERVAL}s[/bold]"
        f"  ·  idle threshold [bold]{IDLE_THRESHOLD}s[/bold]"
    )
    console.print("  Press [bold]Ctrl+C[/bold] to stop.\n")

    prev_app = None

    while _running:
        idle_secs = get_idle_seconds()
        is_idle = idle_secs > IDLE_THRESHOLD

        win = get_active_window()

        if win:
            record(
                app_name=win["app_name"],
                window_title=win["window_title"],
                exe_path=win["exe_path"],
                idle=is_idle,
            )

            label = win["app_name"]
            if is_idle:
                label = f"[dim]{label} (idle {idle_secs:.0f}s)[/dim]"

            # Only print when the focused app changes to keep output readable
            if label != prev_app:
                console.print(f"  [cyan]→[/cyan] {label}")
                prev_app = label

        time.sleep(POLL_INTERVAL)

    console.print("\n[bold]Argus stopped.[/bold] Data saved to ~/.argus/argus.db")


# endregion
