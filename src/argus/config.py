"""Runtime configuration, persistent settings, and app-to-category mapping."""

# region Imports

import json
import os
from pathlib import Path

# endregion

# region Constants

DATA_DIR = Path(os.environ.get("ARGUS_DATA", Path.home() / ".argus"))
DB_PATH  = DATA_DIR / "argus.db"
# Text exports from `argus report` / `argus week` (plain text, alongside the database).
REPORTS_DIR = DATA_DIR / "reports"

_SETTINGS_PATH = DATA_DIR / "settings.json"

POLL_INTERVAL = 5    # seconds between snapshots
IDLE_THRESHOLD = 60  # seconds of no input before marking as idle

# Process name prefix → display category (case-insensitive prefix or substring match)
CATEGORIES: dict[str, list[str]] = {
    "Browser": [
        # Windows
        "chrome", "firefox", "msedge", "opera", "brave", "vivaldi", "iexplore",
        # Linux
        "chromium", "chromium-browser", "firefox-esr", "epiphany", "midori",
        # macOS
        "safari", "arc",
    ],
    "IDE / Editor": [
        # Cross-platform
        "code", "cursor", "pycharm", "idea", "clion", "rider", "vim", "nvim",
        "sublime_text", "atom", "zed", "geany", "emacs",
        # Windows
        "notepad++",
        # Linux
        "gedit", "kate", "mousepad", "xed", "pluma",
        # macOS
        "xcode", "nova",
    ],
    "Terminal": [
        # Windows
        "windowsterminal", "cmd", "powershell", "wt", "conhost",
        # Cross-platform
        "alacritty", "kitty", "wezterm", "hyper",
        # Linux
        "bash", "zsh", "fish", "gnome-terminal", "konsole", "xterm", "xfce4-terminal",
        "tilix", "terminator", "urxvt", "st",
        # macOS
        "iterm2", "terminal",
    ],
    "Communication": [
        "discord", "slack", "teams", "zoom", "skype", "telegram", "signal",
        "whatsapp", "mattermost", "element", "hexchat", "thunderbird",
    ],
    "Design": [
        "figma", "photoshop", "illustrator", "blender", "inkscape", "gimp",
        "krita", "xd", "sketch", "affinity",
    ],
    "Gaming": [
        "steam", "epicgameslauncher", "gog", "origin", "battlenet", "leagueclient",
        "gameoverlayui", "lutris", "heroic",
    ],
    "Productivity": [
        # Cross-platform
        "notion", "obsidian", "evernote", "thunderbird",
        # Windows / Office
        "excel", "word", "powerpoint", "onenote", "outlook",
        # Linux / LibreOffice
        "libreoffice", "soffice", "lowriter", "scalc", "simpress",
        # macOS
        "pages", "numbers", "keynote",
    ],
    "Media": [
        "spotify", "vlc", "mpv", "mpc-hc", "netflix", "plex", "musicbee",
        "foobar2000", "rhythmbox", "clementine", "strawberry", "lollypop",
        "totem", "celluloid",
    ],
    "File Manager": [
        # Windows
        "explorer", "totalcmd", "doublecmd", "xplorer2",
        # Linux
        "nautilus", "dolphin", "thunar", "nemo", "pcmanfm", "ranger", "midnight-commander",
        # macOS
        "finder",
    ],
    "System": [
        # Windows
        "taskmgr", "regedit", "mmc", "services", "eventvwr", "perfmon", "resmon", "dxdiag",
        # Linux
        "htop", "btop", "gnome-system-monitor", "ksysguard", "stacer",
        # macOS
        "activity-monitor",
    ],
}

# endregion

# region Public Methods / API


def load_settings() -> dict:
    """Load persistent settings from disk. Returns an empty dict on any error."""
    if _SETTINGS_PATH.exists():
        try:
            return json.loads(_SETTINGS_PATH.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}


def save_settings(settings: dict) -> None:
    """Merge *settings* into the on-disk file, creating the data directory if needed."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    existing = load_settings()
    existing.update(settings)
    _SETTINGS_PATH.write_text(json.dumps(existing, indent=2, ensure_ascii=False), encoding="utf-8")


def categorise(app_name: str) -> str:
    """Map a process name to its display category.

    Args:
        app_name: Process name (without .exe suffix).

    Returns:
        A category string from CATEGORIES, or "Other" if no match is found.
    """
    lower = app_name.lower()
    for category, patterns in CATEGORIES.items():
        if any(lower.startswith(p) or p in lower for p in patterns):
            return category
    return "Other"


# endregion
