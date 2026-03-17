"""Rich-powered report generation."""

# region Imports

from collections import defaultdict
from datetime import datetime, timedelta

from rich import box
from rich.columns import Columns
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from .config import POLL_INTERVAL, categorise
from .storage import db_stats, query_range

# endregion

# region Fields / Private

console = Console()

# endregion

# region Private Methods


def _fmt(seconds: float) -> str:
    """Format a duration in seconds as a human-readable string (e.g. '1h 05m', '3m 20s')."""
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    if h:
        return f"{h}h {m:02d}m"
    if m:
        return f"{m}m {s:02d}s"
    return f"{s}s"


def _bar(fraction: float, width: int = 24) -> str:
    """Render a filled Unicode progress bar for the given fraction (0.0–1.0)."""
    filled = round(fraction * width)
    return "█" * filled + "░" * (width - filled)


def _aggregate(rows) -> tuple[dict[str, float], dict[str, float]]:
    """Tally snapshot rows into per-app and per-category second totals.

    Args:
        rows: Iterable of sqlite3.Row snapshot records (idle rows excluded upstream).

    Returns:
        Tuple of (app_name → seconds, category → seconds) dicts.
    """
    apps: dict[str, float] = defaultdict(float)
    cats: dict[str, float] = defaultdict(float)
    for row in rows:
        apps[row["app_name"]] += POLL_INTERVAL
        cats[categorise(row["app_name"])] += POLL_INTERVAL
    return dict(apps), dict(cats)


# endregion

# region Public Methods / API


def daily_report(date: datetime) -> None:
    """Print a full daily activity report for the given date.

    Args:
        date: The day to report on; only the date component is used.
    """
    start = datetime(date.year, date.month, date.day)
    end = start + timedelta(days=1)

    rows = query_range(start.timestamp(), end.timestamp())
    apps, cats = _aggregate(rows)
    total_secs = sum(apps.values())

    header = date.strftime("%A, %B %d %Y")
    console.rule(f"[bold cyan]Argus[/bold cyan]  ·  Daily Report  ·  [dim]{header}[/dim]")

    if not rows:
        console.print("\n  [dim]No data recorded for this day.[/dim]\n")
        return

    # region Top Apps table

    app_table = Table(
        title="[bold white]Top Apps[/bold white]",
        box=box.SIMPLE_HEAD,
        header_style="bold cyan",
        show_edge=False,
        min_width=60,
    )
    app_table.add_column("App", style="white", min_width=22)
    app_table.add_column("Time", justify="right", style="bold green", min_width=10)
    app_table.add_column("", min_width=26)
    app_table.add_column("%", justify="right", style="dim", min_width=6)

    for app, secs in sorted(apps.items(), key=lambda x: -x[1])[:15]:
        frac = secs / total_secs if total_secs else 0
        app_table.add_row(app, _fmt(secs), f"[green]{_bar(frac)}[/green]", f"{frac*100:.1f}")

    # endregion

    # region Category Breakdown table

    cat_table = Table(
        title="[bold white]Categories[/bold white]",
        box=box.SIMPLE_HEAD,
        header_style="bold cyan",
        show_edge=False,
        min_width=50,
    )
    cat_table.add_column("Category", style="white", min_width=18)
    cat_table.add_column("Time", justify="right", style="bold yellow", min_width=10)
    cat_table.add_column("", min_width=26)

    for cat, secs in sorted(cats.items(), key=lambda x: -x[1]):
        frac = secs / total_secs if total_secs else 0
        cat_table.add_row(cat, _fmt(secs), f"[yellow]{_bar(frac)}[/yellow]")

    # endregion

    console.print()
    console.print(Columns([app_table, cat_table], padding=(0, 4)))
    console.print(
        Panel(
            f"  Total active time:  [bold green]{_fmt(total_secs)}[/bold green]"
            f"  ·  Snapshots: [dim]{len(rows)}[/dim]  ·  "
            f"Interval: [dim]{POLL_INTERVAL}s[/dim]",
            box=box.SIMPLE,
        )
    )
    console.print()


def weekly_report(anchor: datetime) -> None:
    """Print a 7-day weekly activity report for the week containing anchor.

    Args:
        anchor: Any date within the desired week; the report always starts on Monday.
    """
    monday = anchor - timedelta(days=anchor.weekday())
    monday = datetime(monday.year, monday.month, monday.day)

    console.rule(
        f"[bold cyan]Argus[/bold cyan]  ·  Weekly Report  ·  "
        f"[dim]w/c {monday.strftime('%b %d %Y')}[/dim]"
    )

    week_apps: dict[str, float] = defaultdict(float)
    week_cats: dict[str, float] = defaultdict(float)

    # region Day-by-day table

    day_table = Table(
        title="[bold white]Day-by-day[/bold white]",
        box=box.SIMPLE_HEAD,
        header_style="bold cyan",
        show_edge=False,
    )
    day_table.add_column("Day", style="white", min_width=12)
    day_table.add_column("Active time", justify="right", style="bold green", min_width=10)
    day_table.add_column("Top app", style="dim", min_width=20)

    for offset in range(7):
        day = monday + timedelta(days=offset)
        next_day = day + timedelta(days=1)
        rows = query_range(day.timestamp(), next_day.timestamp())
        apps, cats = _aggregate(rows)

        for k, v in apps.items():
            week_apps[k] += v
        for k, v in cats.items():
            week_cats[k] += v

        total = sum(apps.values())
        top = max(apps, key=apps.get) if apps else "—"
        day_label = day.strftime("%a %d")
        if day.date() == anchor.date():
            day_label = f"[bold]{day_label} ◀[/bold]"

        day_table.add_row(day_label, _fmt(total) if total else "[dim]—[/dim]", top)

    # endregion

    week_total = sum(week_apps.values())

    # region Weekly Categories table

    cat_table = Table(
        title="[bold white]Weekly categories[/bold white]",
        box=box.SIMPLE_HEAD,
        header_style="bold cyan",
        show_edge=False,
        min_width=50,
    )
    cat_table.add_column("Category", style="white", min_width=18)
    cat_table.add_column("Time", justify="right", style="bold yellow", min_width=10)
    cat_table.add_column("", min_width=26)

    for cat, secs in sorted(week_cats.items(), key=lambda x: -x[1]):
        frac = secs / week_total if week_total else 0
        cat_table.add_row(cat, _fmt(secs), f"[yellow]{_bar(frac)}[/yellow]")

    # endregion

    # region Top Apps table

    top_table = Table(
        title="[bold white]Top apps this week[/bold white]",
        box=box.SIMPLE_HEAD,
        header_style="bold cyan",
        show_edge=False,
        min_width=65,
    )
    top_table.add_column("App", style="white", min_width=22)
    top_table.add_column("Time", justify="right", style="bold green", min_width=10)
    top_table.add_column("", min_width=26)
    top_table.add_column("%", justify="right", style="dim", min_width=6)

    for app, secs in sorted(week_apps.items(), key=lambda x: -x[1])[:10]:
        frac = secs / week_total if week_total else 0
        top_table.add_row(app, _fmt(secs), f"[green]{_bar(frac)}[/green]", f"{frac*100:.1f}")

    # endregion

    console.print()
    console.print(Columns([day_table, cat_table], padding=(0, 4)))
    console.print(top_table)
    console.print(
        Panel(
            f"  Weekly active total:  [bold green]{_fmt(week_total)}[/bold green]",
            box=box.SIMPLE,
        )
    )
    console.print()


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
        cat = categorise(win["app_name"])
        body = (
            f"  [bold]App:[/bold]      {win['app_name']}\n"
            f"  [bold]Category:[/bold] {cat}\n"
            f"  [bold]Window:[/bold]   {win['window_title'][:80]}\n"
            f"  [bold]Idle:[/bold]     {idle_label}"
        )
    else:
        body = "  [dim]No active window detected.[/dim]"

    stats = db_stats()
    footer = (
        f"  DB: [dim]{stats['total_snapshots']} snapshots[/dim]"
        if stats["total_snapshots"]
        else "  DB: [dim]empty[/dim]"
    )

    console.print(Panel(body, title="[bold cyan]Argus — Status[/bold cyan]", box=box.ROUNDED))
    console.print(Text(footer, style="dim"))
    console.print()


# endregion
