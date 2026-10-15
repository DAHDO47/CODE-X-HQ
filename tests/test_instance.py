"""Tests fuer die Einmaligkeit der laufenden Instanz.

Zwei Launcher nebeneinander schreiben sich die config.json gegenseitig
zu: jeder haelt seit seinem Start eine eigene Kopie und speichert immer
die ganze Datei. Wer zuletzt speichert, gewinnt - der andere verliert
Sortierung, Projektordner oder Konsolen-Design.
"""

from __future__ import annotations

import uuid

import pytest
from PySide6.QtWidgets import QApplication

from projecthq.ui import instance


@pytest.fixture(scope="session")
def app():
    return QApplication.instance() or QApplication([])


@pytest.fixture
def name() -> str:
    """Ein eigener Name je Test, damit sie sich nicht gegenseitig stoeren."""
    return f"ProjectHQ-test-{uuid.uuid4().hex}"


# --- Wer darf laufen? ------------------------------------------------------


def test_the_first_start_takes_the_name(name):
    token = instance.claim(name)
    assert token is not None
    instance.release(token)


def test_the_second_start_comes_back_empty(name):
    """Der eigentliche Punkt: ein zweiter Launcher entsteht gar nicht erst."""
    token = instance.claim(name)
    try:
        assert instance.claim(name) is None
    finally:
        instance.release(token)


def test_the_name_is_free_again_afterwards(name):
    """Sonst sperrte ein Absturz den naechsten Start dauerhaft aus."""
    instance.release(instance.claim(name))

    token = instance.claim(name)
    assert token is not None
    instance.release(token)


def test_releasing_nothing_is_harmless(name):
    instance.release(None)


# --- Wie sagt es der zweite dem ersten? ------------------------------------


def test_waking_finds_nobody_when_nothing_runs(app, name):
    assert instance.wake_running_instance(name, timeout_ms=200) is False


def test_waking_reaches_the_running_instance(app, name):
    server = instance.listen(name)
    woken = []
    server.newConnection.connect(lambda: woken.append(True))
    try:
        assert instance.wake_running_instance(name) is True
        server.waitForNewConnection(1000)
        assert woken == [True]
    finally:
        server.close()
