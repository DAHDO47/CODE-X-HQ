"""Tests fuer den eigenen Fensterrahmen.

Die reine Rechnung - welche Kante liegt unter der Maus, welche Geometrie
ergibt ein Zug daran - ist ohne Qt-Fenster pruefbar. Dazu kommen
Durchstiche gegen das echte Hauptfenster und die Dialoge: sie sollen
rahmenlos sein und ihre Leiste selbst mitbringen.
"""

from __future__ import annotations

import pytest
from PySide6.QtCore import QPoint, QRect, QSize, Qt
from PySide6.QtWidgets import QApplication, QDialog, QPushButton

from projecthq.config import Config
from projecthq.ui import frame
from projecthq.ui.dialogs import _PromptDialog
from projecthq.ui.window import MainWindow


@pytest.fixture(scope="session")
def app():
    return QApplication.instance() or QApplication([])


@pytest.fixture
def win(app, tmp_path) -> MainWindow:
    root = tmp_path / "projekte"
    (root / "Tarkov").mkdir(parents=True)
    config = Config()
    config.projects_root = root
    return MainWindow(config, tmp_path / "config.json")


RECT = QRect(0, 0, 200, 100)


# --- Kanten und Zeiger ----------------------------------------------------


@pytest.mark.parametrize(
    "point",
    [
        QPoint(100, 50),  # Mitte
        QPoint(1, 50),  # linker Rand
        QPoint(198, 50),  # rechter Rand, aber nicht unten
        QPoint(100, 2),  # oberer Rand
        QPoint(100, 97),  # unterer Rand, aber nicht rechts
        QPoint(0, 0),  # obere linke Ecke
        QPoint(199, 0),  # obere rechte Ecke
        QPoint(0, 99),  # untere linke Ecke
    ],
)
def test_only_the_bottom_right_corner_is_a_grip(point):
    """Der Doppelpfeil sprang frueher an jedem Rand an - auch dicht neben
    den Fensterknoepfen. Ausserhalb der Ecke unten rechts bleibt es jetzt
    beim Pfeil."""
    assert not frame.edges_at(RECT, point)


def test_the_grip_covers_the_bottom_right_corner():
    assert frame.edges_at(RECT, QPoint(199, 99)) == (Qt.BottomEdge | Qt.RightEdge)
    assert frame.edges_at(RECT, QPoint(190, 90)) == (Qt.BottomEdge | Qt.RightEdge)


def test_the_grip_size_is_configurable():
    assert not frame.edges_at(RECT, QPoint(190, 90), size=5)


def test_cursor_follows_the_edge():
    assert frame.cursor_for(frame.NO_EDGE) == Qt.ArrowCursor
    assert frame.cursor_for(Qt.LeftEdge) == Qt.SizeHorCursor
    assert frame.cursor_for(Qt.TopEdge) == Qt.SizeVerCursor
    assert frame.cursor_for(Qt.LeftEdge | Qt.TopEdge) == Qt.SizeFDiagCursor
    assert frame.cursor_for(Qt.RightEdge | Qt.TopEdge) == Qt.SizeBDiagCursor


# --- Ziehen ---------------------------------------------------------------


def test_dragging_the_right_edge_widens():
    start = QRect(10, 10, 200, 100)
    result = frame._resized(start, Qt.RightEdge, QPoint(40, 0), QSize(50, 50))
    assert result == QRect(10, 10, 240, 100)


def test_dragging_the_left_edge_keeps_the_right_side_put():
    start = QRect(10, 10, 200, 100)
    result = frame._resized(start, Qt.LeftEdge, QPoint(30, 0), QSize(50, 50))
    assert result.right() == start.right()
    assert result.left() == 40


def test_a_drag_never_falls_below_the_minimum_size():
    start = QRect(0, 0, 200, 100)
    # Weit ueber die gegenueberliegende Kante hinaus gezogen.
    result = frame._resized(start, Qt.RightEdge, QPoint(-900, 0), QSize(120, 60))
    assert result.width() == 120


# --- Hauptfenster ---------------------------------------------------------


def test_main_window_has_no_system_frame(win):
    assert win.windowFlags() & Qt.FramelessWindowHint


def test_main_window_brings_its_own_titlebar(win):
    assert win.chrome.titlebar is not None
    assert win.chrome.titlebar.label.text() == "CODE/X HQ"


def test_close_button_closes_the_window(win):
    win.show()
    close = [
        button
        for button in win.chrome.titlebar.findChildren(QPushButton)
        if button.objectName() == "chromeClose"
    ]
    assert close, "kein Schliessen-Knopf in der Leiste"
    close[0].click()
    assert not win.isVisible()


def test_maximize_button_toggles_and_swaps_its_glyph(win):
    win.show()
    titlebar = win.chrome.titlebar
    assert titlebar.maximize_button.text() == frame.GLYPH_MAXIMIZE

    titlebar.toggle_maximized()
    assert win.isMaximized()
    assert titlebar.maximize_button.text() == frame.GLYPH_RESTORE

    titlebar.toggle_maximized()
    assert not win.isMaximized()
    assert titlebar.maximize_button.text() == frame.GLYPH_MAXIMIZE


def test_the_main_window_has_a_resize_grip(win):
    assert win.chrome.grip is not None


def test_maximizing_hides_the_grip(win):
    win.show()
    assert win.chrome.grip.isVisible()

    win.showMaximized()
    assert not win.chrome.grip.isVisible()

    win.showNormal()
    assert win.chrome.grip.isVisible()


def test_the_grip_sits_in_the_bottom_right_corner(win):
    win.show()
    win.resize(500, 400)
    grip = win.chrome.grip
    assert grip.pos() == QPoint(
        win.chrome.width() - frame.GRIP_SIZE, win.chrome.height() - frame.GRIP_SIZE
    )


def test_scanlines_cover_the_titlebar_too(win):
    # Das Overlay haengt am Rahmen, nicht am Inhalt darunter - sonst
    # bliebe die eigene Leiste als glatter Streifen stehen.
    assert win.overlay.parentWidget() is win.chrome


# --- Dialoge --------------------------------------------------------------


def test_dialogs_are_frameless_too(win):
    dialog = _PromptDialog(win, "TITEL", "> Hinweis:", "wert")
    assert dialog.windowFlags() & Qt.FramelessWindowHint
    assert isinstance(dialog, QDialog)


def test_dialogs_have_no_resize_grip(win):
    """Ein Dialog fester Groesse braucht keinen Griff, der nichts bewirkt."""
    dialog = _PromptDialog(win, "TITEL", "> Hinweis:", "wert")
    chrome = dialog.findChild(frame.Chrome)
    assert chrome is not None
    assert chrome.grip is None


def test_dialog_titlebar_has_no_minimize_or_maximize(win):
    dialog = _PromptDialog(win, "TITEL", "> Hinweis:", "wert")
    titlebar = dialog.findChild(frame.TitleBar)
    assert titlebar is not None
    assert titlebar.label.text() == "TITEL"
    assert titlebar.maximize_button is None
    glyphs = {button.text() for button in titlebar.findChildren(QPushButton)}
    assert glyphs == {frame.GLYPH_CLOSE}
