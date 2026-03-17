"""Win32-based active window and idle time detection."""

# region Imports

import ctypes
import ctypes.wintypes
from typing import TypedDict

import psutil
import win32gui
import win32process

# endregion

# region Fields / Private


class _LASTINPUTINFO(ctypes.Structure):
    """Win32 LASTINPUTINFO structure used to query the last input event time."""
    _fields_ = [
        ("cbSize", ctypes.wintypes.UINT),
        ("dwTime", ctypes.wintypes.DWORD),
    ]


# endregion

# region Public Methods / API


class WindowInfo(TypedDict):
    """Snapshot of the currently active window."""
    app_name: str
    window_title: str
    exe_path: str


def get_active_window() -> WindowInfo | None:
    """Return info about the current foreground window.

    Returns:
        A WindowInfo dict with app_name, window_title, and exe_path,
        or None if the foreground window cannot be determined.
    """
    try:
        hwnd = win32gui.GetForegroundWindow()
        if not hwnd:
            return None

        window_title = win32gui.GetWindowText(hwnd)
        _, pid = win32process.GetWindowThreadProcessId(hwnd)

        try:
            proc = psutil.Process(pid)
            exe_path = proc.exe()
            app_name = proc.name().removesuffix(".exe")
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            exe_path = ""
            app_name = "unknown"

        return WindowInfo(app_name=app_name, window_title=window_title, exe_path=exe_path)

    except Exception:
        return None


def get_idle_seconds() -> float:
    """Return seconds elapsed since the last keyboard or mouse input.

    Returns:
        Idle duration in seconds (minimum 0.0).
    """
    lii = _LASTINPUTINFO()
    lii.cbSize = ctypes.sizeof(_LASTINPUTINFO)
    ctypes.windll.user32.GetLastInputInfo(ctypes.byref(lii))
    elapsed_ms = ctypes.windll.kernel32.GetTickCount() - lii.dwTime
    return max(0.0, elapsed_ms / 1000.0)


# endregion
