"""Eigener Fensterrahmen im CRT-Look.

Die Titelleiste von Windows bricht den Terminal-Look, deshalb laufen alle
Fenster rahmenlos (`Qt.FramelessWindowHint`) und bringen ihren Rahmen
selbst mit: eine duenne Phosphorlinie aussen, darueber eine Leiste mit
dem Titel in Versalien und Knoepfen aus Terminalzeichen.

Verschieben und Groessenaenderung laufen zuerst ueber `startSystemMove`
und `startSystemResize`. Das ist wichtig, weil damit die Gesten von
Windows erhalten bleiben: an den Bildschirmrand ziehen dockt an, die
Fensterschatten und das Aero-Snap-Raster funktionieren weiter. Nur wenn
der Fenstergriff das ablehnt - etwa unter der Offscreen-Plattform in den
Tests - rechnet `_manual_*` die neue Geometrie selbst aus.

Der Doppelpfeil zum Ziehen erschien frueher an jedem Rand, auch dicht
neben den Fensterknoepfen - dort sprang der Zeiger unbeabsichtigt um.
Gezogen werden kann deshalb nur noch an der Ecke unten rechts, dort
markiert das schraffierte Griffmuster genau die Stelle.
"""

from __future__ import annotations

from PySide6.QtCore import QEvent, QPoint, QRect, Qt
from PySide6.QtGui import QColor, QPainter
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from .. import theme

# Hoehe der eigenen Titelleiste und Breite der Knoepfe darin.
TITLEBAR_HEIGHT = 32
BUTTON_WIDTH = 44

# Innenabstand des Rahmens - der schmale Streifen, in dem aussen die
# Phosphorlinie sitzt.
RESIZE_MARGIN = 6

# Kantenlaenge des Griffs unten rechts, der einzigen Stelle, an der sich
# die Groesse noch ziehen laesst. Grosszuegiger als `RESIZE_MARGIN`,
# sonst waere die Ecke kaum zu treffen.
GRIP_SIZE = 16

# Zeichen der Knoepfe. Bewusst aus dem Vorrat, den Consolas sicher hat -
# ein fehlendes Glyph waere ein leeres Kaestchen.
GLYPH_MINIMIZE = "─"
GLYPH_MAXIMIZE = "□"
GLYPH_RESTORE = "▫"
GLYPH_CLOSE = "×"

NO_EDGE = Qt.Edge(0)


def edges_at(rect: QRect, pos: QPoint, size: int = GRIP_SIZE) -> Qt.Edge:
    """Ob `pos` im Griff unten rechts liegt - ueberall sonst `NO_EDGE`,
    auch an den uebrigen Raendern und Ecken."""
    corner = QRect(rect.right() - size + 1, rect.bottom() - size + 1, size, size)
    return (Qt.BottomEdge | Qt.RightEdge) if corner.contains(pos) else NO_EDGE


def cursor_for(edges: Qt.Edge) -> Qt.CursorShape:
    """Passender Mauszeiger zu den getroffenen Kanten."""
    horizontal = bool(edges & (Qt.LeftEdge | Qt.RightEdge))
    vertical = bool(edges & (Qt.TopEdge | Qt.BottomEdge))
    if horizontal and vertical:
        # Von links oben nach rechts unten laeuft der Zeiger wie ein '\'.
        falling = edges in (Qt.LeftEdge | Qt.TopEdge, Qt.RightEdge | Qt.BottomEdge)
        return Qt.SizeFDiagCursor if falling else Qt.SizeBDiagCursor
    if horizontal:
        return Qt.SizeHorCursor
    if vertical:
        return Qt.SizeVerCursor
    return Qt.ArrowCursor


def _resized(start: QRect, edges: Qt.Edge, delta: QPoint, minimum) -> QRect:
    """Neue Geometrie beim Ziehen an `edges`, ohne unter `minimum` zu fallen.

    `right` und `bottom` eines QRect sind einschliessliche Koordinaten:
    die Breite ist `right - left + 1`. Die Grenzen unten tragen dieses
    Pixel deshalb mit, sonst bliebe das Fenster eins zu breit stehen.
    """
    rect = QRect(start)
    if edges & Qt.LeftEdge:
        rect.setLeft(min(rect.left() + delta.x(), rect.right() - minimum.width() + 1))
    if edges & Qt.RightEdge:
        rect.setRight(max(rect.right() + delta.x(), rect.left() + minimum.width() - 1))
    if edges & Qt.TopEdge:
        rect.setTop(min(rect.top() + delta.y(), rect.bottom() - minimum.height() + 1))
    if edges & Qt.BottomEdge:
        rect.setBottom(max(rect.bottom() + delta.y(), rect.top() + minimum.height() - 1))
    return rect


class TitleBar(QWidget):
    """Eigene Titelleiste: Titel links, Fensterknoepfe rechts."""

    def __init__(
        self,
        window: QWidget,
        title: str,
        *,
        minimize: bool = True,
        maximize: bool = True,
    ) -> None:
        super().__init__()
        self.setObjectName("titlebar")
        self.setFixedHeight(TITLEBAR_HEIGHT)
        self._window = window
        self._allow_maximize = maximize
        self._drag_offset: QPoint | None = None
        self.maximize_button: QPushButton | None = None

        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 0, 0, 0)
        layout.setSpacing(0)

        self.label = QLabel(title)
        self.label.setObjectName("titletext")
        layout.addWidget(self.label)
        layout.addStretch(1)

        if minimize:
            layout.addWidget(self._button(GLYPH_MINIMIZE, window.showMinimized))
        if maximize:
            self.maximize_button = self._button(GLYPH_MAXIMIZE, self.toggle_maximized)
            layout.addWidget(self.maximize_button)
        layout.addWidget(self._button(GLYPH_CLOSE, window.close, name="chromeClose"))

    def _button(self, text: str, slot, *, name: str = "chrome") -> QPushButton:
        button = QPushButton(text)
        button.setObjectName(name)
        # Ohne das wanderte der Tastaturfokus beim Klick in die Leiste.
        button.setFocusPolicy(Qt.NoFocus)
        button.setFixedSize(BUTTON_WIDTH, TITLEBAR_HEIGHT)
        button.clicked.connect(slot)
        return button

    def toggle_maximized(self) -> None:
        if self._window.isMaximized():
            self._window.showNormal()
        else:
            self._window.showMaximized()
        self.update_maximize_glyph()

    def update_maximize_glyph(self) -> None:
        if self.maximize_button is None:
            return
        maximized = self._window.isMaximized()
        self.maximize_button.setText(GLYPH_RESTORE if maximized else GLYPH_MAXIMIZE)

    # --- Verschieben ----------------------------------------------------

    def mousePressEvent(self, event) -> None:  # noqa: N802 (Qt-Namensschema)
        if event.button() != Qt.LeftButton or self._window.isMaximized():
            return
        handle = self._window.windowHandle()
        if handle is not None and handle.startSystemMove():
            return
        origin = event.globalPosition().toPoint()
        self._drag_offset = origin - self._window.frameGeometry().topLeft()

    def mouseMoveEvent(self, event) -> None:  # noqa: N802 (Qt-Namensschema)
        if self._drag_offset is None:
            return
        self._window.move(event.globalPosition().toPoint() - self._drag_offset)

    def mouseReleaseEvent(self, event) -> None:  # noqa: N802 (Qt-Namensschema)
        self._drag_offset = None

    def mouseDoubleClickEvent(self, event) -> None:  # noqa: N802 (Qt-Namensschema)
        if self._allow_maximize and event.button() == Qt.LeftButton:
            self.toggle_maximized()


class _Grip(QWidget):
    """Schraffiertes Griffmuster unten rechts, drei Rillen wie am
    klassischen Fenstergriff.

    Liegt ueber dem Inhalt - deshalb ein eigenes Widget und keine
    Zeichnung im Hintergrund von `Chrome`: der waere an dieser Stelle
    laengst vom Inhalt ueberdeckt. Mausereignisse laesst der Griff selbst
    unbehandelt durch, `Chrome` behandelt Ziehen und Zeiger schon fuer die
    ganze Ecke.
    """

    LINES = 3
    GAP = 4
    PAD = 3

    def __init__(self, chrome: "Chrome") -> None:
        super().__init__(chrome)
        self._chrome = chrome
        self.setFixedSize(GRIP_SIZE, GRIP_SIZE)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)

    def paintEvent(self, event) -> None:  # noqa: N802 (Qt-Namensschema)
        painter = QPainter(self)
        active = self._chrome._window.isActiveWindow()
        painter.setPen(QColor(theme.GREEN if active else theme.DIM))
        for i in range(1, self.LINES + 1):
            offset = self.PAD + i * self.GAP
            painter.drawLine(
                GRIP_SIZE - offset, GRIP_SIZE - self.PAD,
                GRIP_SIZE - self.PAD, GRIP_SIZE - offset,
            )


class Chrome(QWidget):
    """Rahmen um den Fensterinhalt: Phosphorlinie, Leiste, Groessengriff."""

    def __init__(
        self,
        window: QWidget,
        content: QWidget,
        title: str | None,
        *,
        resizable: bool = True,
        minimize: bool = True,
        maximize: bool = True,
    ) -> None:
        super().__init__()
        self.setObjectName("chromeFrame")
        self._window = window
        self._resizable = resizable
        self._resize_edges = NO_EDGE
        self._resize_origin = QPoint()
        self._resize_start = QRect()

        # Ohne Verfolgung kaeme der Zeiger erst beim Klick an, und der
        # Mauszeiger wechselte nie zum Pfeil mit den Pfeilspitzen.
        self.setMouseTracking(True)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(
            RESIZE_MARGIN, RESIZE_MARGIN, RESIZE_MARGIN, RESIZE_MARGIN
        )
        layout.setSpacing(0)

        self.titlebar: TitleBar | None = None
        if title is not None:
            self.titlebar = TitleBar(
                window, title, minimize=minimize, maximize=maximize
            )
            layout.addWidget(self.titlebar)
        layout.addWidget(content, 1)

        # Nur, wo sich ueberhaupt ziehen laesst - ein Dialog fester Groesse
        # braucht keinen Griff, der nichts bewirkt.
        self.grip: _Grip | None = _Grip(self) if resizable else None
        if self.grip is not None:
            self.grip.raise_()

        # Der Rahmen leuchtet nur im aktiven Fenster. Die Meldung darueber
        # geht ans Fenster, nicht an den Rahmen.
        window.installEventFilter(self)

    # --- Aussehen -------------------------------------------------------

    def paintEvent(self, event) -> None:  # noqa: N802 (Qt-Namensschema)
        painter = QPainter(self)
        active = self._window.isActiveWindow()
        painter.setPen(QColor(theme.GREEN if active else theme.DIM))
        painter.drawRect(self.rect().adjusted(0, 0, -1, -1))

    def resizeEvent(self, event) -> None:  # noqa: N802 (Qt-Namensschema)
        super().resizeEvent(event)
        if self.grip is not None:
            self.grip.move(self.width() - GRIP_SIZE, self.height() - GRIP_SIZE)

    def eventFilter(self, watched, event) -> bool:  # noqa: N802 (Qt-Namensschema)
        if watched is self._window:
            if event.type() == QEvent.ActivationChange:
                self.update()
                if self.grip is not None:
                    self.grip.update()
            elif event.type() == QEvent.WindowStateChange:
                if self.titlebar:
                    self.titlebar.update_maximize_glyph()
                # Maximiert laesst sich nicht mehr ziehen - der Griff soll
                # dann auch nicht mehr so aussehen, als koennte er das.
                if self.grip is not None:
                    self.grip.setVisible(not self._window.isMaximized())
        return False

    # --- Groesse aendern ------------------------------------------------

    def _edges_under(self, pos: QPoint) -> Qt.Edge:
        if not self._resizable or self._window.isMaximized():
            return NO_EDGE
        return edges_at(self.rect(), pos)

    def mouseMoveEvent(self, event) -> None:  # noqa: N802 (Qt-Namensschema)
        position = event.position().toPoint()
        if self._resize_edges:
            delta = event.globalPosition().toPoint() - self._resize_origin
            self._window.setGeometry(
                _resized(
                    self._resize_start,
                    self._resize_edges,
                    delta,
                    self._window.minimumSize(),
                )
            )
            return
        self.setCursor(cursor_for(self._edges_under(position)))

    def mousePressEvent(self, event) -> None:  # noqa: N802 (Qt-Namensschema)
        edges = (
            self._edges_under(event.position().toPoint())
            if event.button() == Qt.LeftButton
            else NO_EDGE
        )
        if not edges:
            # Nicht am Rand geklickt: der Rahmen hat damit nichts zu tun,
            # also weiterreichen. Der Boot-Schirm etwa bricht bei jedem
            # Klick ab und braucht das Ereignis.
            event.ignore()
            return
        handle = self._window.windowHandle()
        if handle is not None and handle.startSystemResize(edges):
            return
        self._resize_edges = edges
        self._resize_origin = event.globalPosition().toPoint()
        self._resize_start = self._window.geometry()

    def mouseReleaseEvent(self, event) -> None:  # noqa: N802 (Qt-Namensschema)
        if not self._resize_edges:
            event.ignore()
            return
        self._resize_edges = NO_EDGE

    def leaveEvent(self, event) -> None:  # noqa: N802 (Qt-Namensschema)
        self.unsetCursor()


def wrap(
    window: QWidget,
    content: QWidget,
    title: str | None = None,
    *,
    resizable: bool = True,
    minimize: bool = True,
    maximize: bool = True,
) -> Chrome:
    """Nimmt `window` den Systemrahmen und legt `content` in einen eigenen.

    Der zurueckgegebene Rahmen ist noch nicht eingebaut - das Fenster
    setzt ihn selbst als zentrales Element beziehungsweise in sein
    Layout, je nachdem was es ist.
    """
    window.setWindowFlags(window.windowFlags() | Qt.FramelessWindowHint)
    return Chrome(
        window,
        content,
        title,
        resizable=resizable,
        minimize=minimize,
        maximize=maximize,
    )
