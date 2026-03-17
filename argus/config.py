"""Runtime configuration and app-to-category mapping."""

# region Imports

import os
from pathlib import Path

# endregion

# region Constants

DATA_DIR = Path(os.environ.get("ARGUS_DATA", Path.home() / ".argus"))
DB_PATH = DATA_DIR / "argus.db"

POLL_INTERVAL = 5    # seconds between snapshots
IDLE_THRESHOLD = 60  # seconds of no input before marking as idle

# Process name prefix → display category (case-insensitive prefix or substring match)
CATEGORIES: dict[str, list[str]] = {
    "Browser":       ["chrome", "firefox", "msedge", "opera", "brave", "vivaldi", "iexplore"],
    "IDE / Editor":  ["code", "cursor", "pycharm", "idea", "clion", "rider", "vim", "nvim",
                      "sublime_text", "notepad++", "atom", "zed"],
    "Terminal":      ["windowsterminal", "cmd", "powershell", "wt", "alacritty", "conhost", "bash"],
    "Communication": ["discord", "slack", "teams", "zoom", "skype", "telegram", "signal",
                      "whatsapp", "mattermost"],
    "Design":        ["figma", "photoshop", "illustrator", "blender", "inkscape", "gimp",
                      "krita", "xd", "sketch"],
    "Gaming":        ["steam", "epicgameslauncher", "gog", "origin", "battlenet", "leagueclient",
                      "gameoverlayui"],
    "Productivity":  ["excel", "word", "powerpoint", "onenote", "notion", "obsidian",
                      "evernote", "outlook", "thunderbird"],
    "Media":         ["spotify", "vlc", "mpv", "mpc-hc", "netflix", "plex", "musicbee",
                      "foobar2000"],
    "File Manager":  ["explorer", "totalcmd", "doublecmd", "xplorer2"],
    "System":        ["taskmgr", "regedit", "mmc", "services", "eventvwr", "perfmon",
                      "resmon", "dxdiag"],
}

# endregion

# region Public Methods / API


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
