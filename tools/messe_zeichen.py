"""Misst, wie breit die Symbole der Liste wirklich gemalt werden.

Die Spalten des Launchers stehen auf einem Raster aus gleich breiten
Zeichen. Keines der benutzten Symbole steckt in Consolas selbst; sie
kommen aus der einspringenden Ersatzschrift, und die haelt sich nicht
ans Raster. Ein zu breites Zeichen schiebt alle Spalten seiner Zeile
nach rechts.

Die Testsuite kann das nicht pruefen: sie laeuft mit
``QT_QPA_PLATFORM=offscreen``, und dort meldet Qt ohne echte
Schriftdatenbank fuer jedes Zeichen dieselbe Breite. Deshalb dieses
Werkzeug - es braucht einen richtigen Bildschirm.

    py -3.12 tools\\messe_zeichen.py

Meldet Rueckgabecode 1, wenn ein in `window.GRID_MARKS` zugelassenes
Zeichen nicht auf die Grundbreite passt.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

if os.environ.get("QT_QPA_PLATFORM") == "offscreen":
    raise SystemExit(
        "Offscreen hat keine Schriftdatenbank - so misst dieses Werkzeug nichts."
    )

from PySide6.QtGui import QFont  # noqa: E402
from PySide6.QtWidgets import QApplication, QListWidget  # noqa: E402

from projecthq.theme import stylesheet  # noqa: E402
from projecthq.ui import window as w  # noqa: E402


def main() -> int:
    app = QApplication(sys.argv)
    app.setStyleSheet(stylesheet())

    # Gemessen wird an einer fertig gestylten Liste: das Stylesheet setzt
    # eine Schriftgroesse und uebergeht damit `setFont`. Nur diese Metrik
    # passt zu den Zeichen, die der Nutzer sieht.
    liste = QListWidget()
    liste.setFont(QFont(*w.LIST_FONT))
    liste.setStyleSheet(stylesheet())
    liste.ensurePolished()
    metrics = liste.fontMetrics()
    grund = metrics.horizontalAdvance("0")
    print(f"Schrift: {liste.font().family()}, Grundbreite {grund} px\n")

    benutzt = {
        "Pfeil (ROW_PREFIX)": w.ROW_PREFIX.strip(),
        "Favorit (FAVORITE_PREFIX)": w.FAVORITE_PREFIX.strip(),
        "Notiz (NOTE_MARK)": w.NOTE_MARK,
        "keine Notiz (NO_NOTE_MARK)": w.NO_NOTE_MARK,
        "kein Agent (NO_AGENT_MARK)": w.NO_AGENT_MARK,
    }
    from projecthq.config import AGENT_MARKS

    benutzt.update({f"Agent {name}": mark for name, mark in AGENT_MARKS.items()})

    fehler = 0
    print("--- Was die Liste benutzt ---")
    for name, zeichen in benutzt.items():
        breite = metrics.horizontalAdvance(zeichen)
        passt = breite == grund
        fehler += not passt
        print(f"  {'OK' if passt else '!!'} U+{ord(zeichen):04X} {breite:3d} px  {name}")

    print("\n--- Was GRID_MARKS zulaesst ---")
    for zeichen in sorted(w.GRID_MARKS):
        breite = metrics.horizontalAdvance(zeichen)
        passt = breite == grund
        fehler += not passt
        print(f"  {'OK' if passt else '!!'} U+{ord(zeichen):04X} {breite:3d} px")

    if fehler:
        print(f"\n{fehler} Zeichen passen nicht auf {grund} px.")
        return 1
    print("\nAlles auf dem Raster.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
