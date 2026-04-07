# Argus

**README languages:** English · [日本語](README.ja.md) · [中文](README.zh.md)

> *Named after Argus Panoptes — the hundred-eyed giant of Greek mythology who never slept and watched everything.*

A Python tool that silently records which app and window you have active every 5 seconds. Run it in the background, then pull up a live dashboard or a rich terminal report to see exactly where your time goes.

## Screenshots

Live **TUI** on Windows (`argus tui`): status strip, today’s app and category breakdown with bars, and the weekly table. Left: **Gruvbox**; right: another built-in dark theme (teal palette). Press `T` to cycle themes.

![Argus TUI dashboard — Gruvbox theme](docs/screenshots/tui-dashboard-gruvbox.png)

![Argus TUI dashboard — teal dark theme](docs/screenshots/tui-dashboard-teal.png)

---

## Design rationale

From a systems engineer's perspective, Argus follows a layered design process:

```
Feature Design → Requirements Definition → Basic Design → Detailed Design
```

---

### Feature Design

Features are split into two axes: **Functional** (what it does) and **Non-Functional / Quality Attributes** (how well it behaves).

#### Functional features

| # | Feature | Rationale |
|---|---|---|
| F1 | Track foreground window | Core value — passive, silent, always-on |
| F2 | Auto-categorise apps | Turns raw process names into meaningful categories |
| F3 | Store snapshots in SQLite | Simple, portable, zero-config, no server |
| F4 | Run tracker inside TUI process | Single `argus tui` starts everything, no separate daemon |
| F5 | Auto-start on login | Frictionless — tracking begins without user action |
| F6 | Multi-language TUI (6 languages) | Accessibility for non-English speakers |
| F7 | 12 colour themes | Personalisation without code changes |

#### Non-functional features (quality attributes)

| # | Quality | Target | Driven by |
|---|---|---|---|
| NF1 | **Privacy** — all data stays local | No network, no cloud, no telemetry | User trust |
| NF2 | **Availability** — cross-platform | Windows, macOS, Linux | Platform diversity |
| NF3 | **Performance** — lightweight | < 1 % CPU on a typical desktop | Always-on constraint |
| NF4 | **Availability** — idle detection | Skip snapshots when user is away | Data cleanliness |
| NF5 | **Performance** — low storage overhead | One row per 5-second snapshot | Long-term feasibility |
| NF6 | **Maintainability** — modular design | Clear layer separation | Extensibility |

---

### Requirements Definition

Derived directly from the feature table above.

| Requirement | Source | Target |
|---|---|---|
| Track active windows | F1 | Every 5 seconds, silently |
| Detect and skip idle periods | F1 + NF4 | Exclude away-time from reports |
| Categorise apps automatically | F2 | 11 built-in categories |
| Persist all snapshots locally | F3 | SQLite in `~/.argus/` |
| Single-process TUI with embedded tracker | F4 | No separate background service |
| Auto-start on login | F5 | OS-specific registration |
| Multi-language UI | F6 | 6 languages, saved to settings |
| 12 colour themes | F7 | Press `T` to cycle |
| Local-only, no network | NF1 | Privacy guarantee |
| Cross-platform | NF2 | Win / macOS / Linux |
| CPU under 1 % | NF3 | On typical desktop hardware |
| Modular / extensible | NF6 | Separate layers and modules |

### Basic Design — three layers

```
┌─────────────────────────────────────────────┐
│  UI layer: TUI (Textual) + Reports (Rich)  │
├─────────────────────────────────────────────┤
│  Service layer: Tracker, Storage, Report    │
├─────────────────────────────────────────────┤
│  Platform layer: Win32 / macOS / Linux     │
└─────────────────────────────────────────────┘
```

### Detailed Design — module responsibilities

| Module | Responsibility |
|---|---|
| `tracker.py` | Platform-specific active window + idle detection |
| `storage.py` | SQLite init, `record()` write, `query_range()` read |
| `daemon.py` | Foreground polling loop (`start` command) |
| `tui.py` | Textual dashboard + embedded background poller |
| `report.py` | Daily / weekly Rich reports + status panel |
| `autostart.py` | OS-specific login-item registration |
| `config.py` | Constants, category map, settings persistence |
| `i18n.py` | UI string catalogue (6 languages) |

---

## Architecture diagrams

The following [Mermaid](https://mermaid.js.org/) blocks render natively on GitHub. They document the module structure, key types, the tracking polling loop, and the `report` command call sequence.

### Sequence diagram — `report`

```mermaid
sequenceDiagram
    actor User
    participant CLI as main.py
    participant Report as report.py
    participant Storage as storage.py
    participant Rich as Rich console
    User->>CLI: report optional date
    CLI->>Report: daily_report(datetime)
    Report->>Storage: query_range(start, end)
    Storage-->>Report: snapshot rows
    Report->>Report: aggregate and categorise
    Report->>Rich: tables and panels
    Rich-->>User: terminal output
```

### Module structure

High-level dependency flow: `main.py` delegates to each `argus/` module.

```mermaid
flowchart LR
    subgraph entry[Entry]
        main[main.py]
    end
    subgraph pkg[argus package]
        config[config.py]
        tracker[tracker.py]
        storage[storage.py]
        daemon[daemon.py]
        report[report.py]
        tui[tui.py]
        autostart[autostart.py]
        i18n[i18n.py]
    end
    main --> daemon
    main --> report
    main --> tui
    main --> autostart
    main --> tracker
    daemon --> tracker
    daemon --> storage
    daemon --> config
    tui --> tracker
    tui --> storage
    tui --> config
    tui --> report
    tui --> autostart
    tui --> i18n
    report --> storage
    report --> config
    autostart --> config
    storage --> config
```

### Class diagram

`WindowInfo` is the TypedDict snapshot shape returned by the tracker; TUI screens subclass Textual widgets.

```mermaid
classDiagram
    direction TB
    class App
    class Static
    class ModalScreen
    App <|-- ArgusApp
    Static <|-- StatusWidget
    ModalScreen <|-- HelpScreen
    ModalScreen <|-- WelcomeScreen
    class WindowInfo {
        <<TypedDict>>
        app_name
        window_title
        exe_path
    }
    note for App "textual.app.App"
    note for Static "textual.widgets.Static"
    note for ModalScreen "textual.screen.ModalScreen"
```

### Activity diagram — tracking loop

Shared logic for the `start` / daemon and the TUI background poller: poll interval → idle check → record snapshot → wait → repeat.

```mermaid
flowchart TD
    A([Start tracker]) --> B[init_db]
    B --> C{Still running?}
    C -->|yes| D[get_idle_seconds]
    D --> E[get_active_window]
    E --> F{Foreground window known?}
    F -->|yes| G[record snapshot]
    F -->|no| H[Skip write]
    G --> I[Wait POLL_INTERVAL]
    H --> I
    I --> C
    C -->|no / interrupt| J([Stop])
```

---

## Quickstart

### Windows

```bash
# Download dist/argus.exe and run
argus.exe tui
```

### macOS

```bash
# Download dist/argus and run
./argus tui
```

### Linux

```bash
# Install system dependencies first
sudo apt install xdotool xprintidle   # Ubuntu / Debian
sudo dnf install xdotool xprintidle   # Fedora

# Download dist/argus and run
./argus tui
```

### What to do next

```bash
# View today's activity report
argus tui        # Interactive dashboard (recommended)
argus report     # Text report in terminal

# View specific day
argus report --date 2026-04-05

# View this week's report
argus week

# Check what you're doing right now
argus status

# Auto-start on login
argus install    # Enable auto-start
argus uninstall  # Disable auto-start
```

---

## Keyboard shortcuts (TUI)

| Key | Action |
|---|---|
| `R` | Refresh data immediately |
| `T` | Cycle through colour themes |
| `L` | Cycle through UI languages (6 languages) |
| `A` | Toggle Auto Start |
| `O` | Open the data folder |
| `[` `]` | Previous / next day |
| `{` `}` | Previous / next week |
| `Q` | Quit |

---

## TUI dashboard

`argus tui` opens a live full-terminal dashboard powered by [Textual](https://textual.textualize.io/). It also runs the tracker in the background — no separate `start` command needed.

**What it shows**

- **Status panel** — active app, category, window title, idle time, and total snapshot count
- **Today** — top 10 apps and category breakdown with progress bars
- **This Week** — day-by-day summary table plus weekly top apps and categories

Everything auto-refreshes every 5 seconds.

---

## Languages

The TUI supports 6 languages, cycled with `L`:

`en` (English) · `ja` (日本語) · `zh` (中文) · `fr` (Français) · `de` (Deutsch) · `es` (Español)

Your language choice is saved to `~/.argus/settings.json` and restored on next launch.

---

## Themes

Press `T` in the TUI to cycle through all 12 built-in Textual themes:

`textual-dark` · `textual-light` · `nord` · `gruvbox` · `catppuccin-mocha` · `catppuccin-latte` · `dracula` · `tokyo-night` · `monokai` · `solarized-dark` · `solarized-light` · `flexoki`

Your theme choice is saved and restored automatically.

---

## Data

Everything is stored in `~/.argus/argus.db` (SQLite) by default (override the folder with env `ARGUS_DATA`). One row per 5-second snapshot:

| Column | Type | Description |
|---|---|---|
| `ts` | REAL | Unix timestamp |
| `app_name` | TEXT | Process name (e.g. `chrome`, `code`) |
| `window_title` | TEXT | Window title at that moment |
| `exe_path` | TEXT | Full path to the executable |
| `idle` | INTEGER | 1 if no input for longer than the idle threshold |

Idle snapshots are excluded from all reports and the TUI by default.

User preferences (language, theme) are stored separately in `~/.argus/settings.json`.

---

## Categories

Apps are automatically bucketed into categories:

`Browser` · `IDE / Editor` · `Terminal` · `Communication` · `Design` · `Gaming` · `Productivity` · `Media` · `File Manager` · `System` · `Other`

To add or change mappings, edit the `CATEGORIES` dict in `argus/config.py`.

---

## Stack

| Concern | Tool |
|---|---|
| Active window detection | `pywin32` (Windows) · `osascript` (macOS) · `xdotool` (Linux) |
| Idle detection | `GetLastInputInfo` via ctypes (Windows) · `ioreg` (macOS) · `xprintidle` (Linux) |
| Process info | `psutil` |
| Storage | SQLite via stdlib `sqlite3` |
| CLI | `Typer` |
| Terminal reports | `Rich` |
| Interactive dashboard | `Textual` |
| Auto-start | Registry key (Windows) · LaunchAgent plist (macOS) · XDG autostart (Linux) |

---

## Setup & Building (for experienced users)

> These sections are for developers who want to run from source or build their own executable.

### Setup (development)

```bash
pip install -r requirements.txt
```

**Linux only** — install two extra system packages for window and idle detection:

```bash
sudo apt install xdotool xprintidle   # Ubuntu / Debian
sudo dnf install xdotool xprintidle   # Fedora
```

### Building a standalone executable

Packages Argus into a single file that end users can run with no Python or pip required.

```bash
# Install build tools (one-time)
pip install -r requirements-dev.txt

# Build
python build.py
```

Output lands in `dist/`:

| Platform | File |
|---|---|
| Windows | `dist/argus.exe` |
| Linux | `dist/argus` |
| macOS | `dist/argus` |

The executable is fully self-contained — Python, Textual, Rich, and all other dependencies are bundled inside it. **End users need to install nothing.**

> **Linux note:** `xdotool` and `xprintidle` are system packages that cannot be bundled. Include the following in any Linux distribution:
> ```bash
> sudo apt install xdotool xprintidle
> ```

### Usage (from source)

```bash
# Interactive dashboard (recommended — also runs the tracker in the background)
python src/main.py tui

# Start the tracker alone in the foreground (Ctrl+C to stop)
python src/main.py start

# Today's activity report
python src/main.py report

# Report for a specific day
python src/main.py report --date 2026-03-15

# This week's report
python src/main.py week

# What are you doing right now?
python src/main.py status

# Register Argus to launch automatically at login
python src/main.py install

# Remove from auto-start
python src/main.py uninstall
```

---

## Tuning

Edit the two constants at the top of `argus/config.py`:

```python
POLL_INTERVAL  = 5    # seconds between snapshots
IDLE_THRESHOLD = 60   # seconds of no input before a snapshot is marked idle
```

---

## Project structure

```
src/
├── main.py               # Typer CLI — thin entry point, delegates to argus/
└── argus/
    ├── __init__.py       # package version
    ├── config.py         # constants, category map, settings persistence
    ├── i18n.py           # UI string catalogue (6 languages)
    ├── tracker.py        # active window + idle detection (Win / macOS / Linux)
    ├── storage.py        # SQLite read/write
    ├── daemon.py         # foreground polling loop (used by `start` command)
    ├── report.py         # Rich daily/weekly/status reports
    ├── tui.py            # Textual live dashboard
    └── autostart.py      # login auto-start helpers (Win / macOS / Linux)
build.py                  # PyInstaller build script → dist/argus[.exe]
requirements.txt          # runtime dependencies
requirements-dev.txt      # runtime + build tools (pyinstaller)
dist/                     # compiled executables (git-ignored)
```
