"""Textual TUI for Argus — single-page dashboard with integrated live tracking."""

# region Imports

from __future__ import annotations

import os
import subprocess
import sys
import threading
from datetime import datetime, timedelta

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Center, Horizontal, ScrollableContainer, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, DataTable, Footer, Header, Label, Rule, Static

from .autostart import is_enabled as autostart_is_enabled
from .autostart import toggle as autostart_toggle
from .config import DATA_DIR, IDLE_THRESHOLD, POLL_INTERVAL, categorise
from .config import load_settings, save_settings
from .i18n import LANGUAGES, cycle_language, get_language, set_language, t
from .report import _aggregate, _bar, _fmt
from .storage import db_stats, init_db, query_range, record

# endregion

# region Constants

_UI_REFRESH = 5.0  # seconds between UI auto-refreshes

# Built-in Textual themes — all ship with the library, no extras needed.
_THEMES: list[str] = [
    "textual-dark",
    "textual-light",
    "nord",
    "gruvbox",
    "catppuccin-mocha",
    "catppuccin-latte",
    "dracula",
    "tokyo-night",
    "monokai",
    "solarized-dark",
    "solarized-light",
    "flexoki",
]

# endregion

# region Background Polling

_stop_event = threading.Event()


def _start_polling() -> None:
    """Spawn a daemon thread that polls the active window and writes snapshots to the DB.

    Uses a threading.Event so the loop exits cleanly when the TUI closes.
    Signal handlers are intentionally omitted — they must only run on the main thread.
    """
    def _loop() -> None:
        from .tracker import get_active_window, get_idle_seconds

        init_db()
        while not _stop_event.wait(POLL_INTERVAL):
            try:
                idle = get_idle_seconds()
                win = get_active_window()
                if win:
                    record(
                        app_name=win["app_name"],
                        window_title=win["window_title"],
                        exe_path=win["exe_path"],
                        idle=idle > IDLE_THRESHOLD,
                    )
            except Exception:
                pass

    threading.Thread(target=_loop, name="argus-poll", daemon=True).start()


# endregion

# region Helpers


def _autostart_label() -> str:
    """Return the Auto Start button label reflecting the current state."""
    try:
        enabled = autostart_is_enabled()
    except Exception:
        enabled = False
    return t("auto_start_on") if enabled else t("auto_start_off")


def _lang_label() -> str:
    """Return the language button label, e.g. 'EN  English'."""
    code = get_language()
    return f"{code.upper()}  {LANGUAGES[code]}"


# endregion

# region Widgets


class StatusWidget(Static):
    """Live panel showing the current foreground window, category, idle state, and DB size."""

    def refresh_data(self) -> None:
        """Re-query and redraw with the latest window and idle info."""
        try:
            from .tracker import get_active_window, get_idle_seconds

            win = get_active_window()
            idle = get_idle_seconds()
        except Exception:
            win = None
            idle = 0.0

        stats = db_stats()
        snap_text = f"{stats['total_snapshots']:,}" if stats["total_snapshots"] else "0"

        if win:
            cat = categorise(win["app_name"])
            idle_label = (
                f"[bold red]{t('idle', f'{idle:.0f}')}[/]"
                if idle > IDLE_THRESHOLD
                else f"[green]{t('active_sec', f'{idle:.0f}')}[/]"
            )
            title = win["window_title"]
            if len(title) > 68:
                title = title[:68] + "…"
            content = (
                f"  [bold cyan]{t('app')}[/]       {win['app_name']}     "
                f"[bold cyan]{t('category')}[/]  {cat}\n"
                f"  [bold cyan]{t('window')}[/]    {title}\n"
                f"  [bold cyan]{t('idle_header')}[/]      {idle_label}     "
                f"[bold cyan]{t('snapshots')}[/]  {snap_text}"
            )
        else:
            content = (
                f"  [dim]{t('no_window')}[/]\n"
                f"  [bold cyan]{t('snapshots')}[/]  {snap_text}"
            )

        self.update(content)


# endregion

# region Modal Screens


class HelpScreen(ModalScreen):
    """Keyboard-shortcut reference card — press ? or Esc to close."""

    BINDINGS = [Binding("escape,question_mark", "dismiss", "Close")]

    CSS = """
    HelpScreen {
        align: center middle;
    }
    #help-box {
        width: 64;
        height: auto;
        border: round $primary;
        background: $surface;
        padding: 1 2;
    }
    #help-box .help-heading {
        text-style: bold;
        color: $primary;
        margin: 1 0 0 0;
    }
    #help-box .help-hint {
        color: $text-disabled;
        margin: 1 0 0 0;
        text-align: center;
    }
    """

    def compose(self) -> ComposeResult:
        with Vertical(id="help-box"):
            yield Label("Argus — Help", classes="help-heading")
            yield Rule()
            yield Static(
                "  [bold cyan]?[/]   This help screen\n"
                "  [bold cyan]R[/]   Refresh all data\n"
                "  [bold cyan]T[/]   Cycle colour theme\n"
                "  [bold cyan]L[/]   Cycle language\n"
                "  [bold cyan]A[/]   Toggle Auto Start (launch at login)\n"
                "  [bold cyan]O[/]   Open folder where Argus saves files\n"
                "  [bold cyan]Q[/]   Quit\n"
                "  [dim]Dashboard: ◀ ▶ plus Today / This week browse past days & weeks (see footer keys).[/]"
            )
            yield Rule()
            yield Label("Toolbar buttons", classes="help-heading")
            yield Static(
                f"  [dim]Auto Start ON/OFF[/]   toggle login auto-start\n"
                f"  [dim]EN  English[/]          cycle language\n"
                f"  [dim]Open saved data folder[/]   database and settings under [cyan]{DATA_DIR}[/]"
            )
            yield Rule()
            yield Label("Data", classes="help-heading")
            yield Static(
                f"  Snapshot every [cyan]{POLL_INTERVAL}s[/]  "
                f"·  idle >[cyan]{IDLE_THRESHOLD}s[/] excluded from reports\n"
                f"  Database: [dim]{DATA_DIR / 'argus.db'}[/]\n"
                f"  Use ◀ ▶ and Today / This week to browse past days and weeks."
            )
            yield Label("Press [bold]Esc[/] or [bold]?[/] to close", classes="help-hint")

    def on_key(self, _) -> None:
        self.dismiss()


class WelcomeScreen(ModalScreen):
    """First-run onboarding overlay — shown once, dismissed with 'Get Started'."""

    CSS = """
    WelcomeScreen {
        align: center middle;
    }
    #welcome-box {
        width: 56;
        height: auto;
        border: round $primary;
        background: $surface;
        padding: 1 2;
    }
    #welcome-title {
        text-style: bold;
        color: $primary;
        text-align: center;
        margin: 0 0 1 0;
    }
    #welcome-box .welcome-section {
        text-style: bold;
        color: $accent;
        margin: 1 0 0 0;
    }
    #btn-start {
        margin: 1 0 0 0;
        width: 100%;
    }
    """

    def compose(self) -> ComposeResult:
        with Vertical(id="welcome-box"):
            yield Label("Welcome to Argus", id="welcome-title")
            yield Static(
                "  Argus quietly records which app and window you\n"
                "  have active every 5 seconds — so you always know\n"
                "  exactly where your time goes."
            )
            yield Rule()
            yield Label("Getting started", classes="welcome-section")
            yield Static(
                "  [cyan]*[/] The dashboard is already updating live\n"
                "  [cyan]*[/] Press [bold]T[/] to change the colour theme\n"
                "  [cyan]*[/] Press [bold]L[/] to change the language\n"
                "  [cyan]*[/] Press [bold]A[/] to enable Auto Start at login\n"
                "  [cyan]*[/] Press [bold]?[/] anytime to see all shortcuts\n"
                "  [cyan]*[/] Press [bold]Q[/] to quit"
            )
            with Center():
                yield Button(t("get_started") + "  →", id="btn-start", variant="primary")

    def on_button_pressed(self, _: Button.Pressed) -> None:
        self.dismiss()


# endregion

# region App


class ArgusApp(App):
    """Argus dashboard — live status plus browsable daily and weekly history."""

    TITLE = "Argus"

    CSS = """
    Screen {
        background: $surface;
    }

    #scroll {
        padding: 0 1;
    }

    StatusWidget {
        border: round $primary;
        padding: 1 2;
        margin: 1 0;
        height: auto;
    }

    Rule {
        margin: 1 0 0 0;
        color: $primary-darken-2;
    }

    .section-label {
        text-style: bold;
        color: $primary;
        margin: 0 0 0 1;
        padding: 0;
    }

    .section-header {
        height: auto;
        align: left middle;
        margin: 0;
        padding: 0;
    }

    .section-header .section-label {
        width: 1fr;
    }

    .nav-row {
        width: auto;
        height: auto;
    }

    Button.nav-btn {
        min-width: 5;
    }

    #btn-day-today, #btn-week-this {
        min-width: 14;
    }

    .summary {
        color: $text-disabled;
        margin: 0 1 1 1;
    }

    .cols {
        height: auto;
        margin: 0;
    }

    .col {
        width: 1fr;
        height: auto;
    }

    DataTable {
        height: auto;
        max-height: 14;
        margin: 0 1 0 0;
    }

    #weekly-days {
        max-height: 9;
        margin: 0 0 1 0;
    }

    #toolbar {
        height: 3;
        align: right middle;
        margin: 0 0 0 0;
        padding: 0 1;
    }

    #db-path {
        width: 1fr;
        content-align: left middle;
        color: $text-disabled;
    }

    #btn-autostart {
        min-width: 20;
    }

    #btn-language {
        min-width: 16;
    }

    #btn-open-db {
        min-width: 16;
    }
    """

    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("r", "refresh", "Refresh"),
        Binding("t", "cycle_theme", "Theme"),
        Binding("l", "cycle_language", "Language"),
        Binding("a", "toggle_autostart", "Auto Start"),
        Binding("o", "open_db_folder", "Data folder"),
        Binding("left_square_bracket", "day_prev", "Day −"),
        Binding("right_square_bracket", "day_next", "Day +"),
        Binding("braceleft", "week_prev", "Week −"),
        Binding("braceright", "week_next", "Week +"),
        Binding("question_mark", "show_help", "Help"),
    ]

    # region Compose

    def compose(self) -> ComposeResult:
        """Build the single-page layout: status → toolbar → today → this week."""
        yield Header(show_clock=True)
        with ScrollableContainer(id="scroll"):
            yield StatusWidget(id="status")
            with Horizontal(id="toolbar"):
                yield Label(str(DATA_DIR), id="db-path")
                yield Button(_autostart_label(), id="btn-autostart")
                yield Button(_lang_label(), id="btn-language")
                yield Button(t("open_db_folder"), id="btn-open-db")

            yield Rule()
            with Horizontal(classes="section-header"):
                yield Label("", id="today-label", classes="section-label")
                with Horizontal(classes="nav-row"):
                    yield Button("◀", id="btn-day-prev", classes="nav-btn")
                    yield Button(t("nav_today"), id="btn-day-today")
                    yield Button("▶", id="btn-day-next", classes="nav-btn")
            with Horizontal(classes="cols"):
                with Vertical(classes="col"):
                    yield DataTable(id="today-apps", show_cursor=False)
                with Vertical(classes="col"):
                    yield DataTable(id="today-cats", show_cursor=False)
            yield Label("", id="today-summary", classes="summary")

            yield Rule()
            with Horizontal(classes="section-header"):
                yield Label("", id="week-label", classes="section-label")
                with Horizontal(classes="nav-row"):
                    yield Button("◀", id="btn-week-prev", classes="nav-btn")
                    yield Button(t("nav_this_week"), id="btn-week-this")
                    yield Button("▶", id="btn-week-next", classes="nav-btn")
            yield DataTable(id="weekly-days", show_cursor=False)
            with Horizontal(classes="cols"):
                with Vertical(classes="col"):
                    yield DataTable(id="weekly-cats", show_cursor=False)
                with Vertical(classes="col"):
                    yield DataTable(id="weekly-apps", show_cursor=False)
            yield Label("", id="week-summary", classes="summary")

        yield Footer()

    # endregion

    # region Initialization

    def on_mount(self) -> None:
        """Add table columns, load initial data, start auto-refresh, and show first-run welcome."""
        self._init_view_state()
        self.sub_title = t("subtitle")
        self._setup_tables()
        self._refresh()
        self.set_interval(_UI_REFRESH, self._refresh)

        # Show the welcome screen once — never again after the first run.
        if not load_settings().get("seen_welcome"):
            self.call_after_refresh(self._show_welcome)

    def _show_welcome(self) -> None:
        def _mark_seen(_) -> None:
            save_settings({"seen_welcome": True})
        self.push_screen(WelcomeScreen(), _mark_seen)

    # endregion

    # region Private Methods

    def _init_view_state(self) -> None:
        """Reset day/week navigation to track the real calendar (live today & this week)."""
        now = datetime.now()
        self._pin_day_to_today = True
        self._pin_week_to_current = True
        self._view_day = datetime(now.year, now.month, now.day)
        m = now - timedelta(days=now.weekday())
        self._week_monday = datetime(m.year, m.month, m.day)

    def _setup_tables(self) -> None:
        """Add column headers to every DataTable (call after language change too)."""
        cols_apps = (t("app"), t("time"), t("bar"), t("pct"))
        cols_cats = (t("category"), t("time"), t("bar"))

        self.query_one("#today-apps",   DataTable).add_columns(*cols_apps)
        self.query_one("#today-cats",   DataTable).add_columns(*cols_cats)
        self.query_one("#weekly-days",  DataTable).add_columns(t("day"), t("active"), t("top_app"))
        self.query_one("#weekly-cats",  DataTable).add_columns(*cols_cats)
        self.query_one("#weekly-apps",  DataTable).add_columns(*cols_apps)

    def _rebuild_for_language(self) -> None:
        """Rebuild all language-sensitive UI after a language switch."""
        self.sub_title = t("subtitle")
        self.query_one("#btn-open-db",   Button).label = t("open_db_folder")
        self.query_one("#btn-language",  Button).label = _lang_label()
        self.query_one("#btn-autostart", Button).label = _autostart_label()
        self.query_one("#btn-day-today", Button).label = t("nav_today")
        self.query_one("#btn-week-this", Button).label = t("nav_this_week")
        for sel in ("#today-apps", "#today-cats", "#weekly-days", "#weekly-cats", "#weekly-apps"):
            self.query_one(sel, DataTable).clear(columns=True)
        self._setup_tables()
        self._refresh()

    def _refresh(self) -> None:
        """Refresh the status widget, today's tables, and the weekly tables."""
        self.query_one(StatusWidget).refresh_data()
        self._refresh_today()
        self._refresh_week()
        self._update_nav_states()

    def _refresh_today(self) -> None:
        """Reload the selected day's app and category tables from the DB."""
        if self._pin_day_to_today:
            n = datetime.now()
            self._view_day = datetime(n.year, n.month, n.day)

        start = self._view_day
        end   = start + timedelta(days=1)
        date_str = start.strftime("%A, %B %d %Y")
        day_heading = (
            t("today_label", date_str) if self._pin_day_to_today else t("day_past_label", date_str)
        )
        self.query_one("#today-label", Label).update(day_heading)

        rows  = query_range(start.timestamp(), end.timestamp())
        apps, cats = _aggregate(rows)
        total = sum(apps.values())

        self._fill_apps("#today-apps", apps, total, limit=10)
        self._fill_cats("#today-cats", cats, total)
        self.query_one("#today-summary", Label).update(
            t("total_active_today", _fmt(total), len(rows))
            if rows
            else t("no_data_today")
        )

    def _refresh_week(self) -> None:
        """Reload the selected week's day-by-day table, categories, and top apps from the DB."""
        if self._pin_week_to_current:
            today = datetime.now()
            m = today - timedelta(days=today.weekday())
            self._week_monday = datetime(m.year, m.month, m.day)

        monday = self._week_monday
        sunday = monday + timedelta(days=6)
        real_today = datetime.now().date()

        if self._pin_week_to_current:
            self.query_one("#week-label", Label).update(
                t("week_label", monday.strftime("%b %d"), sunday.strftime("%b %d, %Y"))
            )
        else:
            self.query_one("#week-label", Label).update(
                t("week_past_label", monday.strftime("%b %d"), sunday.strftime("%b %d, %Y"))
            )

        week_apps: dict[str, float] = {}
        week_cats: dict[str, float] = {}

        days_tbl = self.query_one("#weekly-days", DataTable)
        days_tbl.clear()

        for offset in range(7):
            day      = monday + timedelta(days=offset)
            day_rows = query_range(day.timestamp(), (day + timedelta(days=1)).timestamp())
            apps, cats = _aggregate(day_rows)

            for k, v in apps.items():
                week_apps[k] = week_apps.get(k, 0) + v
            for k, v in cats.items():
                week_cats[k] = week_cats.get(k, 0) + v

            total_day = sum(apps.values())
            top       = max(apps, key=apps.get) if apps else "—"
            day_label = day.strftime("%a %b %d")
            if self._pin_week_to_current and day.date() == real_today:
                day_label = f"▶ {day_label}"
            days_tbl.add_row(day_label, _fmt(total_day) if total_day else "—", top)

        week_total = sum(week_apps.values())
        self._fill_cats("#weekly-cats", week_cats, week_total)
        self._fill_apps("#weekly-apps", week_apps, week_total, limit=10)
        self.query_one("#week-summary", Label).update(
            t("weekly_total", _fmt(week_total))
            if week_total
            else t("no_data_week")
        )

    def _update_nav_states(self) -> None:
        """Disable next buttons when already at the latest day or week."""
        today_d = datetime.now().date()
        vd = self._view_day.date()
        self.query_one("#btn-day-next", Button).disabled = vd >= today_d

        now = datetime.now()
        cur_m = now - timedelta(days=now.weekday())
        cur_m_d = datetime(cur_m.year, cur_m.month, cur_m.day).date()
        wm_d = self._week_monday.date()
        self.query_one("#btn-week-next", Button).disabled = wm_d >= cur_m_d

    def _fill_apps(self, sel: str, apps: dict, total: float, limit: int = 10) -> None:
        """Clear and repopulate an apps DataTable sorted by time descending."""
        tbl = self.query_one(sel, DataTable)
        tbl.clear()
        for name, secs in sorted(apps.items(), key=lambda x: -x[1])[:limit]:
            frac = secs / total if total else 0
            tbl.add_row(name, _fmt(secs), _bar(frac, 20), f"{frac * 100:.1f}%")

    def _fill_cats(self, sel: str, cats: dict, total: float) -> None:
        """Clear and repopulate a categories DataTable sorted by time descending."""
        tbl = self.query_one(sel, DataTable)
        tbl.clear()
        for cat, secs in sorted(cats.items(), key=lambda x: -x[1]):
            frac = secs / total if total else 0
            tbl.add_row(cat, _fmt(secs), _bar(frac, 20))

    # endregion

    # region Public Methods / API

    def action_show_help(self) -> None:
        """Open the keyboard shortcut reference overlay."""
        self.push_screen(HelpScreen())

    def action_refresh(self) -> None:
        """Manually trigger a full refresh of all widgets."""
        self._refresh()

    def action_day_prev(self) -> None:
        """Show the previous calendar day (leave pinned-to-today mode)."""
        if self._pin_day_to_today:
            n = datetime.now()
            self._view_day = datetime(n.year, n.month, n.day) - timedelta(days=1)
            self._pin_day_to_today = False
        else:
            self._view_day -= timedelta(days=1)
        self._refresh_today()
        self._update_nav_states()

    def action_day_next(self) -> None:
        """Show the next calendar day, up to and including today."""
        cap = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        nxt = self._view_day + timedelta(days=1)
        if nxt.date() >= cap.date():
            self._view_day = cap
            self._pin_day_to_today = True
        else:
            self._pin_day_to_today = False
            self._view_day = nxt
        self._refresh_today()
        self._update_nav_states()

    def action_day_today(self) -> None:
        """Jump back to the live current day."""
        self._pin_day_to_today = True
        self._refresh_today()
        self._update_nav_states()

    def action_week_prev(self) -> None:
        """Show the previous ISO week (Monday–Sunday)."""
        self._pin_week_to_current = False
        self._week_monday -= timedelta(days=7)
        self._refresh_week()
        self._update_nav_states()

    def action_week_next(self) -> None:
        """Show the next week, up to the current calendar week."""
        now = datetime.now()
        cur_m = now - timedelta(days=now.weekday())
        cap = datetime(cur_m.year, cur_m.month, cur_m.day)
        nxt = self._week_monday + timedelta(days=7)
        if nxt.date() >= cap.date():
            self._week_monday = cap
            self._pin_week_to_current = True
        else:
            self._pin_week_to_current = False
            self._week_monday = nxt
        self._refresh_week()
        self._update_nav_states()

    def action_week_this(self) -> None:
        """Jump back to the live current week."""
        self._pin_week_to_current = True
        self._refresh_week()
        self._update_nav_states()

    def action_open_db_folder(self) -> None:
        """Open the Argus data directory in the system file manager."""
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        if sys.platform == "win32":
            os.startfile(DATA_DIR)
        elif sys.platform == "darwin":
            subprocess.run(["open", str(DATA_DIR)], check=False)
        else:
            subprocess.run(["xdg-open", str(DATA_DIR)], check=False)

    def action_toggle_autostart(self) -> None:
        """Toggle the system login auto-start and update the button label."""
        try:
            enabled = autostart_toggle()
            self.query_one("#btn-autostart", Button).label = _autostart_label()
            msg = t("autostart_enabled") if enabled else t("autostart_disabled")
            self.notify(msg)
        except Exception as exc:
            self.notify(t("autostart_error", str(exc)), severity="error")

    def action_cycle_language(self) -> None:
        """Advance to the next UI language, persist the choice, and rebuild the UI."""
        code = cycle_language()
        save_settings({"language": code})
        self._rebuild_for_language()

    def action_cycle_theme(self) -> None:
        """Advance to the next built-in Textual theme and persist the choice."""
        try:
            current = self.theme or _THEMES[0]
            idx = _THEMES.index(current) if current in _THEMES else 0
            next_theme = _THEMES[(idx + 1) % len(_THEMES)]
            self.theme = next_theme
            save_settings({"theme": next_theme})
            self.notify(next_theme)
        except Exception as exc:
            self.notify(str(exc), severity="error")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Route button presses to the appropriate action.

        Args:
            event: The button press event carrying the button's ID.
        """
        bid = event.button.id
        if bid == "btn-open-db":
            self.action_open_db_folder()
        elif bid == "btn-autostart":
            self.action_toggle_autostart()
        elif bid == "btn-language":
            self.action_cycle_language()
        elif bid == "btn-day-prev":
            self.action_day_prev()
        elif bid == "btn-day-next":
            self.action_day_next()
        elif bid == "btn-day-today":
            self.action_day_today()
        elif bid == "btn-week-prev":
            self.action_week_prev()
        elif bid == "btn-week-next":
            self.action_week_next()
        elif bid == "btn-week-this":
            self.action_week_this()

    # endregion


# endregion


def run() -> None:
    """Load persisted settings, start background polling, then launch the TUI.

    The polling thread writes snapshots to the DB every POLL_INTERVAL seconds.
    It is stopped cleanly via a threading.Event when the app exits.
    """
    settings = load_settings()
    set_language(settings.get("language", "en"))

    saved_theme = settings.get("theme", _THEMES[0])
    if saved_theme not in _THEMES:
        saved_theme = _THEMES[0]

    _start_polling()
    try:
        app = ArgusApp()
        app.theme = saved_theme
        app.run()
    finally:
        _stop_event.set()
