"""Rich-powered report generation."""

# region Imports

from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path

from rich import box
from rich.columns import Columns
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from .config import POLL_INTERVAL, REPORTS_DIR, categorise
from .storage import db_stats, query_range

# endregion

console = Console()


def _save_report_text(recorder: Console, path: Path) -> None:
    """Write Rich `export_text()` output to disk (UTF-8)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(recorder.export_text(clear=False), encoding="utf-8")

# region Helpers


def _fmt(seconds: float) -> str:
    """Format a duration as a compact human-readable string (e.g. '1h 05m', '3m 20s')."""
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    if h:
        return f"{h}h {m:02d}m"
    if m:
        return f"{m}m {s:02d}s"
    return f"{s}s"


def _bar(fraction: float, width: int = 24) -> str:
    """Render a filled Unicode progress bar for a fraction between 0.0 and 1.0."""
    filled = round(fraction * width)
    return "█" * filled + "░" * (width - filled)


def _table(title: str, min_width: int = 0) -> Table:
    """Create a consistently styled Rich table.

    All report tables share the same box style, header colour, and edge setting.
    Only the title and optional minimum width vary between them.
    """
    kwargs = {"min_width": min_width} if min_width else {}
    return Table(
        title=f"[bold white]{title}[/bold white]",
        box=box.SIMPLE_HEAD,
        header_style="bold cyan",
        show_edge=False,
        **kwargs,
    )


def _aggregate(rows) -> tuple[dict[str, float], dict[str, float]]:
    """Tally snapshot rows into per-app and per-category second totals.

    Each snapshot represents POLL_INTERVAL seconds of activity.

    Returns:
        Tuple of (app_name → seconds, category → seconds).
    """
    apps: dict[str, float] = defaultdict(float)
    cats: dict[str, float] = defaultdict(float)
    for row in rows:
        apps[row["app_name"]] += POLL_INTERVAL
        cats[categorise(row["app_name"])] += POLL_INTERVAL
    return dict(apps), dict(cats)


# endregion

# region Public API


def daily_report(date: datetime) -> None:
    """Print a full daily activity report for the given date.

    Also writes a plain-text copy under ``REPORTS_DIR`` (e.g. ``daily-2026-03-21.txt``).
    """
    rc = Console(record=True, width=120)
    start = datetime(date.year, date.month, date.day)
    rows  = query_range(start.timestamp(), (start + timedelta(days=1)).timestamp())
    apps, cats = _aggregate(rows)
    total = sum(apps.values())

    rc.rule(
        f"[bold cyan]Argus[/bold cyan]  ·  Daily Report  ·  "
        f"[dim]{date.strftime('%A, %B %d %Y')}[/dim]"
    )

    if not rows:
        rc.print("\n  [dim]No data recorded for this day.[/dim]\n")
        out_path = REPORTS_DIR / f"daily-{start.strftime('%Y-%m-%d')}.txt"
        _save_report_text(rc, out_path)
        console.print(f"[dim]Report saved:[/dim] [cyan]{out_path}[/cyan]")
        return

    # Top apps table
    app_tbl = _table("Top Apps", min_width=60)
    app_tbl.add_column("App",  style="white",      min_width=22)
    app_tbl.add_column("Time", style="bold green",  min_width=10, justify="right")
    app_tbl.add_column("",                          min_width=26)
    app_tbl.add_column("%",    style="dim",         min_width=6,  justify="right")
    for app, secs in sorted(apps.items(), key=lambda x: -x[1])[:15]:
        frac = secs / total if total else 0
        app_tbl.add_row(app, _fmt(secs), f"[green]{_bar(frac)}[/green]", f"{frac*100:.1f}")

    # Category breakdown table
    cat_tbl = _table("Categories", min_width=50)
    cat_tbl.add_column("Category", style="white",       min_width=18)
    cat_tbl.add_column("Time",     style="bold yellow",  min_width=10, justify="right")
    cat_tbl.add_column("",                               min_width=26)
    for cat, secs in sorted(cats.items(), key=lambda x: -x[1]):
        frac = secs / total if total else 0
        cat_tbl.add_row(cat, _fmt(secs), f"[yellow]{_bar(frac)}[/yellow]")

    rc.print()
    rc.print(Columns([app_tbl, cat_tbl], padding=(0, 4)))
    rc.print(Panel(
        f"  Total active time:  [bold green]{_fmt(total)}[/bold green]"
        f"  ·  Snapshots: [dim]{len(rows)}[/dim]"
        f"  ·  Interval: [dim]{POLL_INTERVAL}s[/dim]",
        box=box.SIMPLE,
    ))
    rc.print()

    out_path = REPORTS_DIR / f"daily-{start.strftime('%Y-%m-%d')}.txt"
    _save_report_text(rc, out_path)
    console.print(f"[dim]Report saved:[/dim] [cyan]{out_path}[/cyan]")


def weekly_report(anchor: datetime) -> None:
    """Print a 7-day weekly report for the week containing anchor.

    The week always starts on Monday. A plain-text copy is saved under ``REPORTS_DIR``
    (e.g. ``weekly-2026-03-17.txt`` for the Monday of that week).
    """
    rc = Console(record=True, width=120)
    monday = anchor - timedelta(days=anchor.weekday())
    monday = datetime(monday.year, monday.month, monday.day)

    rc.rule(
        f"[bold cyan]Argus[/bold cyan]  ·  Weekly Report  ·  "
        f"[dim]w/c {monday.strftime('%b %d %Y')}[/dim]"
    )

    week_apps: dict[str, float] = defaultdict(float)
    week_cats: dict[str, float] = defaultdict(float)

    # Day-by-day summary table
    day_tbl = _table("Day-by-day")
    day_tbl.add_column("Day",         style="white",      min_width=12)
    day_tbl.add_column("Active time", style="bold green",  min_width=10, justify="right")
    day_tbl.add_column("Top app",     style="dim",         min_width=20)

    for offset in range(7):
        day  = monday + timedelta(days=offset)
        rows = query_range(day.timestamp(), (day + timedelta(days=1)).timestamp())
        apps, cats = _aggregate(rows)

        for k, v in apps.items():
            week_apps[k] += v
        for k, v in cats.items():
            week_cats[k] += v

        total     = sum(apps.values())
        top       = max(apps, key=apps.get) if apps else "—"
        day_label = day.strftime("%a %d")
        if day.date() == anchor.date():
            day_label = f"[bold]{day_label} ◀[/bold]"
        day_tbl.add_row(day_label, _fmt(total) if total else "[dim]—[/dim]", top)

    week_total = sum(week_apps.values())

    # Weekly categories table
    cat_tbl = _table("Weekly categories", min_width=50)
    cat_tbl.add_column("Category", style="white",       min_width=18)
    cat_tbl.add_column("Time",     style="bold yellow",  min_width=10, justify="right")
    cat_tbl.add_column("",                               min_width=26)
    for cat, secs in sorted(week_cats.items(), key=lambda x: -x[1]):
        frac = secs / week_total if week_total else 0
        cat_tbl.add_row(cat, _fmt(secs), f"[yellow]{_bar(frac)}[/yellow]")

    # Top apps this week table
    top_tbl = _table("Top apps this week", min_width=65)
    top_tbl.add_column("App",  style="white",      min_width=22)
    top_tbl.add_column("Time", style="bold green",  min_width=10, justify="right")
    top_tbl.add_column("",                          min_width=26)
    top_tbl.add_column("%",    style="dim",         min_width=6,  justify="right")
    for app, secs in sorted(week_apps.items(), key=lambda x: -x[1])[:10]:
        frac = secs / week_total if week_total else 0
        top_tbl.add_row(app, _fmt(secs), f"[green]{_bar(frac)}[/green]", f"{frac*100:.1f}")

    rc.print()
    rc.print(Columns([day_tbl, cat_tbl], padding=(0, 4)))
    rc.print(top_tbl)
    rc.print(Panel(
        f"  Weekly active total:  [bold green]{_fmt(week_total)}[/bold green]",
        box=box.SIMPLE,
    ))
    rc.print()

    out_path = REPORTS_DIR / f"weekly-{monday.strftime('%Y-%m-%d')}.txt"
    _save_report_text(rc, out_path)
    console.print(f"[dim]Report saved:[/dim] [cyan]{out_path}[/cyan]")


def status_panel(win, idle_secs: float) -> None:
    """Print a live status panel showing the current window and idle state.

    Args:
        win: WindowInfo dict from tracker.get_active_window(), or None.
        idle_secs: Seconds since the last keyboard or mouse input.
    """
    from .config import IDLE_THRESHOLD

    idle_label = (
        f"[bold red]{idle_secs:.1f}s — IDLE[/bold red]"
        if idle_secs > IDLE_THRESHOLD
        else f"[green]{idle_secs:.1f}s[/green]"
    )

    if win:
        cat  = categorise(win["app_name"])
        body = (
            f"  [bold]App:[/bold]      {win['app_name']}\n"
            f"  [bold]Category:[/bold] {cat}\n"
            f"  [bold]Window:[/bold]   {win['window_title'][:80]}\n"
            f"  [bold]Idle:[/bold]     {idle_label}"
        )
    else:
        body = "  [dim]No active window detected.[/dim]"

    stats  = db_stats()
    footer = (
        f"  DB: [dim]{stats['total_snapshots']} snapshots[/dim]"
        if stats["total_snapshots"]
        else "  DB: [dim]empty[/dim]"
    )

    console.print(Panel(body, title="[bold cyan]Argus — Status[/bold cyan]", box=box.ROUNDED))
    console.print(Text(footer, style="dim"))
    console.print()


# endregion
