# Argus 👁

> *Named after Argus Panoptes — the hundred-eyed giant of Greek mythology who never slept and watched everything.*

A Python daemon that silently runs in the background, recording which app and window you have active every 5 seconds. Generates daily and weekly reports so you can understand your own habits: where your time actually goes, what you focus on, and when you drift.

---

## Stack

| Concern | Tool |
|---|---|
| Active window detection | `pywin32` — `GetForegroundWindow` |
| Idle detection | `GetLastInputInfo` via `ctypes` |
| Process info | `psutil` |
| Storage | `SQLite` (stdlib `sqlite3`) |
| CLI | `Typer` |
| Reports | `Rich` (tables, bars, panels) |
| Autostart | Windows Task Scheduler |

---

## Setup

```bash
pip install -r requirements.txt
```

---

## Usage

```bash
# Start the daemon (runs in foreground, Ctrl+C to stop)
python main.py start

# Today's report
python main.py report

# Report for a specific day
python main.py report --date 2026-03-15

# This week's report
python main.py week

# What are you doing right now?
python main.py status

# Add to Windows startup (runs at login)
python main.py install

# Remove from startup
python main.py uninstall
```

---

## Data

Everything is stored in `~/.argus/argus.db` (SQLite). One row per 5-second snapshot:

| Column | Type | Description |
|---|---|---|
| `ts` | REAL | Unix timestamp |
| `app_name` | TEXT | Process name (e.g. `chrome`, `code`) |
| `window_title` | TEXT | Window title at that moment |
| `exe_path` | TEXT | Full path to executable |
| `idle` | INTEGER | 1 if no input for >60s |

Idle snapshots are excluded from all reports by default.

---

## Categories

Apps are automatically grouped into categories for the report:

`Browser` · `IDE / Editor` · `Terminal` · `Communication` · `Design` · `Gaming` · `Productivity` · `Media` · `File Manager` · `System` · `Other`

Customize the mapping in `argus/config.py`.

---

## Tuning

Edit `argus/config.py`:

```python
POLL_INTERVAL = 5    # seconds between snapshots
IDLE_THRESHOLD = 60  # seconds before marking as idle
```

---

## Structure

```
argus/
├── __init__.py
├── config.py      # constants, category mappings
├── tracker.py     # Win32 window + idle detection
├── storage.py     # SQLite read/write
├── daemon.py      # main polling loop
└── report.py      # Rich daily/weekly reports
main.py            # Typer CLI entry point
```
