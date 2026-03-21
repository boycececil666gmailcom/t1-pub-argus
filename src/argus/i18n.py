"""Internationalisation — UI string catalogue for Argus.

Supported language codes
------------------------
en  English
ja  Japanese  (日本語)
zh  Chinese Simplified  (中文简体)
fr  French  (Français)
de  German  (Deutsch)
es  Spanish  (Español)  — the primary language of Mexico and Latin America
"""

from __future__ import annotations

# region Language registry

LANGUAGES: dict[str, str] = {
    "en": "English",
    "ja": "日本語",
    "zh": "中文",
    "fr": "Français",
    "de": "Deutsch",
    "es": "Español",
}

# endregion

# region String catalogue

STRINGS: dict[str, dict[str, str]] = {
    # ── English ───────────────────────────────────────────────────────────────
    "en": {
        "subtitle":             "Activity Tracker",
        "help":                 "Help",
        "get_started":          "Get Started",
        "app":                  "App",
        "time":                 "Time",
        "bar":                  "Bar",
        "pct":                  "%",
        "category":             "Category",
        "day":                  "Day",
        "active":               "Active",
        "top_app":              "Top App",
        "window":               "Window",
        "idle_header":          "Idle",
        "snapshots":            "Snapshots",
        "today_label":          "Today — {}",
        "week_label":           "This Week — {} – {}",
        "total_active_today":   "Total active today: {}  ·  {} snapshots",
        "no_data_today":        "No data recorded today.",
        "weekly_total":         "Weekly active total: {}",
        "no_data_week":         "No data for this week.",
        "open_db_folder":       "Open DB Folder",
        "auto_start_on":        "Auto Start  ON",
        "auto_start_off":       "Auto Start  OFF",
        "autostart_enabled":    "Auto Start enabled — Argus will launch at login.",
        "autostart_disabled":   "Auto Start disabled.",
        "autostart_error":      "Could not toggle Auto Start: {}",
        "no_window":            "No active window detected.",
        "idle":                 "IDLE — {}s",
        "active_sec":           "{}s active",
    },

    # ── Japanese ──────────────────────────────────────────────────────────────
    "ja": {
        "subtitle":             "アクティビティトラッカー",
        "help":                 "ヘルプ",
        "get_started":          "始める",
        "app":                  "アプリ",
        "time":                 "時間",
        "bar":                  "バー",
        "pct":                  "%",
        "category":             "カテゴリ",
        "day":                  "曜日",
        "active":               "アクティブ",
        "top_app":              "主要アプリ",
        "window":               "ウィンドウ",
        "idle_header":          "アイドル",
        "snapshots":            "記録数",
        "today_label":          "今日 — {}",
        "week_label":           "今週 — {} – {}",
        "total_active_today":   "今日の合計: {}  ·  {} 件",
        "no_data_today":        "今日のデータはありません。",
        "weekly_total":         "今週の合計: {}",
        "no_data_week":         "今週のデータはありません。",
        "open_db_folder":       "DBフォルダを開く",
        "auto_start_on":        "自動起動  ON",
        "auto_start_off":       "自動起動  OFF",
        "autostart_enabled":    "自動起動が有効になりました。",
        "autostart_disabled":   "自動起動が無効になりました。",
        "autostart_error":      "自動起動の切替に失敗: {}",
        "no_window":            "アクティブウィンドウが検出されません。",
        "idle":                 "アイドル — {}秒",
        "active_sec":           "{}秒 アクティブ",
    },

    # ── Chinese Simplified ────────────────────────────────────────────────────
    "zh": {
        "subtitle":             "活动追踪器",
        "help":                 "帮助",
        "get_started":          "开始",
        "app":                  "应用",
        "time":                 "时间",
        "bar":                  "进度",
        "pct":                  "%",
        "category":             "类别",
        "day":                  "日期",
        "active":               "活跃",
        "top_app":              "主要应用",
        "window":               "窗口",
        "idle_header":          "闲置",
        "snapshots":            "记录",
        "today_label":          "今天 — {}",
        "week_label":           "本周 — {} – {}",
        "total_active_today":   "今日总计: {}  ·  {} 条",
        "no_data_today":        "今天暂无数据。",
        "weekly_total":         "本周总计: {}",
        "no_data_week":         "本周暂无数据。",
        "open_db_folder":       "打开数据目录",
        "auto_start_on":        "开机自启  开",
        "auto_start_off":       "开机自启  关",
        "autostart_enabled":    "已启用开机自启。",
        "autostart_disabled":   "已禁用开机自启。",
        "autostart_error":      "切换自启失败: {}",
        "no_window":            "未检测到活动窗口。",
        "idle":                 "闲置 — {}秒",
        "active_sec":           "{}秒 活跃",
    },

    # ── French ────────────────────────────────────────────────────────────────
    "fr": {
        "subtitle":             "Suivi d'activité",
        "help":                 "Aide",
        "get_started":          "Commencer",
        "app":                  "Application",
        "time":                 "Durée",
        "bar":                  "Barre",
        "pct":                  "%",
        "category":             "Catégorie",
        "day":                  "Jour",
        "active":               "Actif",
        "top_app":              "Top App",
        "window":               "Fenêtre",
        "idle_header":          "Inactivité",
        "snapshots":            "Captures",
        "today_label":          "Aujourd'hui — {}",
        "week_label":           "Cette semaine — {} – {}",
        "total_active_today":   "Total actif aujourd'hui: {}  ·  {} captures",
        "no_data_today":        "Aucune donnée aujourd'hui.",
        "weekly_total":         "Total hebdomadaire: {}",
        "no_data_week":         "Aucune donnée cette semaine.",
        "open_db_folder":       "Ouvrir dossier DB",
        "auto_start_on":        "Démarrage auto  ON",
        "auto_start_off":       "Démarrage auto  OFF",
        "autostart_enabled":    "Démarrage automatique activé.",
        "autostart_disabled":   "Démarrage automatique désactivé.",
        "autostart_error":      "Impossible de basculer le démarrage auto: {}",
        "no_window":            "Aucune fenêtre active détectée.",
        "idle":                 "INACTIF — {}s",
        "active_sec":           "{}s actif",
    },

    # ── German ────────────────────────────────────────────────────────────────
    "de": {
        "subtitle":             "Aktivitätstracker",
        "help":                 "Hilfe",
        "get_started":          "Loslegen",
        "app":                  "App",
        "time":                 "Zeit",
        "bar":                  "Balken",
        "pct":                  "%",
        "category":             "Kategorie",
        "day":                  "Tag",
        "active":               "Aktiv",
        "top_app":              "Top-App",
        "window":               "Fenster",
        "idle_header":          "Leerlauf",
        "snapshots":            "Einträge",
        "today_label":          "Heute — {}",
        "week_label":           "Diese Woche — {} – {}",
        "total_active_today":   "Heute aktiv: {}  ·  {} Einträge",
        "no_data_today":        "Heute keine Daten erfasst.",
        "weekly_total":         "Wöchentlich aktiv: {}",
        "no_data_week":         "Keine Daten für diese Woche.",
        "open_db_folder":       "DB-Ordner öffnen",
        "auto_start_on":        "Autostart  AN",
        "auto_start_off":       "Autostart  AUS",
        "autostart_enabled":    "Autostart aktiviert.",
        "autostart_disabled":   "Autostart deaktiviert.",
        "autostart_error":      "Autostart konnte nicht umgeschaltet werden: {}",
        "no_window":            "Kein aktives Fenster erkannt.",
        "idle":                 "LEERLAUF — {}s",
        "active_sec":           "{}s aktiv",
    },

    # ── Spanish ───────────────────────────────────────────────────────────────
    # Primary language of Mexico and most of Latin America.
    "es": {
        "subtitle":             "Rastreador de actividad",
        "help":                 "Ayuda",
        "get_started":          "Empezar",
        "app":                  "Aplicación",
        "time":                 "Tiempo",
        "bar":                  "Barra",
        "pct":                  "%",
        "category":             "Categoría",
        "day":                  "Día",
        "active":               "Activo",
        "top_app":              "App principal",
        "window":               "Ventana",
        "idle_header":          "Inactivo",
        "snapshots":            "Registros",
        "today_label":          "Hoy — {}",
        "week_label":           "Esta semana — {} – {}",
        "total_active_today":   "Total activo hoy: {}  ·  {} registros",
        "no_data_today":        "Sin datos hoy.",
        "weekly_total":         "Total semanal: {}",
        "no_data_week":         "Sin datos esta semana.",
        "open_db_folder":       "Abrir carpeta DB",
        "auto_start_on":        "Inicio auto  ON",
        "auto_start_off":       "Inicio auto  OFF",
        "autostart_enabled":    "Inicio automático activado.",
        "autostart_disabled":   "Inicio automático desactivado.",
        "autostart_error":      "No se pudo cambiar el inicio automático: {}",
        "no_window":            "No se detectó ventana activa.",
        "idle":                 "INACTIVO — {}s",
        "active_sec":           "{}s activo",
    },
}

# endregion

# region State

_current_lang: str = "en"

# endregion

# region Public API


def set_language(code: str) -> None:
    """Set the active language. Silently ignores unknown codes."""
    global _current_lang
    if code in STRINGS:
        _current_lang = code


def get_language() -> str:
    """Return the active language code (e.g. 'en', 'ja')."""
    return _current_lang


def cycle_language() -> str:
    """Advance to the next language in rotation and return the new code."""
    global _current_lang
    codes = list(LANGUAGES)
    idx = codes.index(_current_lang) if _current_lang in codes else 0
    _current_lang = codes[(idx + 1) % len(codes)]
    return _current_lang


def t(key: str, *args: object) -> str:
    """Translate *key* in the active language, optionally formatting with *args*.

    Falls back to the English catalogue, then to the bare key string.
    """
    catalogue = STRINGS.get(_current_lang, STRINGS["en"])
    template = catalogue.get(key) or STRINGS["en"].get(key) or key
    return template.format(*args) if args else template


# endregion
