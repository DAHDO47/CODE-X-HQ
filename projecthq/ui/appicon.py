"""Anwendungssymbol fuer Fenster und Taskleiste.

Die `.ico` liegt im Entwicklungsbetrieb unter `assets/` im Projektordner
und im Build im `_internal`-Verzeichnis neben der `.exe`; `icon_path`
kennt beide Faelle. Fehlt die Datei, laeuft das Programm ohne eigenes
Symbol weiter, statt beim Start zu scheitern.
"""

from __future__ import annotations

import ctypes
import sys
from pathlib import Path

from PySide6.QtGui import QIcon

# Ohne eigene Modell-ID haengt Windows die Fenster unter dem Symbol des
# Python-Interpreters in der Taskleiste ein statt unter unserem eigenen.
APP_ID = "codexhq.projecthq.launcher"

ICON_NAME = "projecthq.ico"


def icon_path() -> Path | None:
    """Pfad zur `.ico`, oder None, wenn sie nicht mitgeliefert wurde."""
    if getattr(sys, "frozen", False):
        base = Path(getattr(sys, "_MEIPASS", Path(sys.executable).parent))
    else:
        base = Path(__file__).resolve().parents[2]
    candidate = base / "assets" / ICON_NAME
    return candidate if candidate.is_file() else None


def set_app_user_model_id() -> bool:
    """Meldet Windows eine eigene Anwendungs-ID. Liefert den Erfolg."""
    if not sys.platform.startswith("win"):
        return False
    try:
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(APP_ID)
    except (AttributeError, OSError):
        return False
    return True


def apply_app_icon(app) -> bool:
    """Setzt das Symbol fuer alle Fenster der Anwendung."""
    set_app_user_model_id()
    path = icon_path()
    if path is None:
        return False
    icon = QIcon(str(path))
    if icon.isNull():
        return False
    app.setWindowIcon(icon)
    return True
