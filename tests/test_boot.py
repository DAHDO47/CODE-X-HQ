"""Tests fuer die Boot-Sequenz.

Sie sieht nur aus wie Zierrat, traegt aber Ablauflogik: sie schreibt Zeile
um Zeile, endet von selbst und laesst sich jederzeit ueberspringen. Genau
das steht hier - wie sie aussieht, nicht.
"""

from __future__ import annotations

import pytest
from PySide6.QtCore import Qt
from PySide6.QtGui import QKeyEvent
from PySide6.QtWidgets import QApplication

from projecthq.ui.boot import LINES, BootScreen


@pytest.fixture(scope="session")
def app():
    return QApplication.instance() or QApplication([])


@pytest.fixture
def boot(app) -> BootScreen:
    screen = BootScreen()
    screen.done = []
    screen.finished.connect(lambda: screen.done.append(True))
    return screen


def run_to_the_end(screen: BootScreen) -> None:
    """Alle Zeilen schreiben und den Schirm auslaufen lassen."""
    for _ in range(len(LINES) + 1):
        screen._tick()


def test_every_tick_writes_the_next_line(boot):
    boot._tick()
    assert boot.label.text() == LINES[0]

    boot._tick()
    assert boot.label.text() == f"{LINES[0]}\n{LINES[1]}"


def test_the_screen_finishes_after_the_last_line(boot):
    run_to_the_end(boot)
    assert boot.done == [True]


def test_it_writes_every_line_and_not_one_more(boot):
    """Ohne Grenze liefe der Index ueber das Ende von LINES hinaus."""
    for _ in range(len(LINES) + 10):
        boot._tick()
    assert boot.label.text() == "\n".join(LINES)
    assert boot.done == [True]


def test_finishing_a_second_time_stays_quiet(boot):
    """Klick und Timer koennen zusammenfallen - gemeldet wird trotzdem einmal."""
    boot._finish()
    boot._finish()
    assert boot.done == [True]


def test_a_click_skips_the_rest(boot):
    boot.mousePressEvent(None)
    assert boot.done == [True]


def test_a_key_skips_the_rest(boot):
    boot.keyPressEvent(
        QKeyEvent(QKeyEvent.KeyPress, Qt.Key_Space, Qt.NoModifier)
    )
    assert boot.done == [True]


def test_the_timer_stops_when_the_screen_is_done(boot):
    boot.start()
    assert boot._timer.isActive()
    boot._finish()
    assert not boot._timer.isActive()
