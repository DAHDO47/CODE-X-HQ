"""Boot-Sequenz im BIOS-Stil, überspringbar per Klick oder Taste."""

from __future__ import annotations

from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget

from .. import theme
from ..i18n import tr
from .frame import wrap

LINES = [
    "CODE/X HQ BIOS v1.0   (C) 2026",
    "",
    "Speichertest .............. OK",
    "Dateisystem ............... OK",
    "Projektindex .............. OK",
    "Terminal-Emulation ........ OK",
    "",
    "Starte CODE/X HQ ...",
]


class BootScreen(QWidget):
    finished = Signal()

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("CODE/X HQ")
        self.resize(980, 680)
        self.setStyleSheet(f"background: {theme.BG}; color: {theme.GREEN};")

        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(40, 40, 40, 40)

        self.label = QLabel("")
        self.label.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self.label.setStyleSheet(
            "font-family: Consolas, 'Courier New', monospace; "
            f"font-size: 15px; color: {theme.GREEN};"
        )
        layout.addWidget(self.label, 1)

        hint = QLabel(tr("[ Klick oder Taste zum Überspringen ]"))
        hint.setStyleSheet(f"color: {theme.DIM}; font-size: 11px;")
        hint.setAlignment(Qt.AlignRight)
        layout.addWidget(hint)

        # Kein Titelbalken: der Schirm laeuft eine Sekunde und bricht bei
        # jedem Klick ab, Knoepfe waeren nur im Weg.
        chrome = wrap(self, content, None, resizable=False)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(chrome)

        self._index = 0
        self._done = False
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)

    def start(self) -> None:
        self.show()
        self._timer.start(110)

    def _tick(self) -> None:
        if self._index >= len(LINES):
            self._finish()
            return
        current = self.label.text()
        line = tr(LINES[self._index])
        self.label.setText(f"{current}\n{line}" if current else line)
        self._index += 1

    def _finish(self) -> None:
        if self._done:
            return
        self._done = True
        self._timer.stop()
        self.finished.emit()
        self.close()

    def mousePressEvent(self, event) -> None:  # noqa: N802 (Qt-Namensschema)
        self._finish()

    def keyPressEvent(self, event) -> None:  # noqa: N802 (Qt-Namensschema)
        self._finish()
