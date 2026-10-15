"""Scanline- und Vignetten-Overlay über dem Hauptfenster.

Das Overlay ist mausdurchlässig (`WA_TransparentForMouseEvents`), damit
es Klicks auf die darunterliegenden Bedienelemente nicht abfängt.
"""

from __future__ import annotations

from PySide6.QtCore import QPointF, Qt
from PySide6.QtGui import QColor, QPainter, QRadialGradient
from PySide6.QtWidgets import QWidget


class CRTOverlay(QWidget):
    def __init__(self, parent: QWidget) -> None:
        super().__init__(parent)
        self.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        self.setAttribute(Qt.WA_NoSystemBackground, True)
        self.setAttribute(Qt.WA_TranslucentBackground, True)

    def resize_to_parent(self) -> None:
        parent = self.parentWidget()
        if parent is not None:
            self.setGeometry(parent.rect())
            self.raise_()

    def paintEvent(self, event) -> None:  # noqa: N802 (Qt-Namensschema)
        painter = QPainter(self)
        rect = self.rect()

        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(0, 0, 0, 38))
        for y in range(0, rect.height(), 3):
            painter.drawRect(0, y, rect.width(), 1)

        gradient = QRadialGradient(
            QPointF(rect.center()), max(rect.width(), rect.height()) * 0.75
        )
        gradient.setColorAt(0.0, QColor(0, 0, 0, 0))
        gradient.setColorAt(0.7, QColor(0, 0, 0, 40))
        gradient.setColorAt(1.0, QColor(0, 0, 0, 160))
        painter.setBrush(gradient)
        painter.drawRect(rect)
