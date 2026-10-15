"""Tests fuer den Einstiegspunkt.

`main` ist duenn, aber es ist die einzige Stelle, an der die Einmaligkeit
der Instanz, die Uebernahme der Einstellungen und die Boot-Sequenz
zusammenkommen. Geht sie kaputt, startet das Programm nicht mehr - oder,
schlimmer, es startet und sperrt sich selbst aus.

Gepruegt wird ohne Ereignisschleife: `exec` gibt sofort zurueck, und der
Namensanspruch laeuft nicht gegen den echten, damit ein laufendes
ProjectHQ den Testlauf nicht beeinflusst.
"""

from __future__ import annotations

import json
import uuid

import pytest
from PySide6.QtWidgets import QApplication

import main as entry
from projecthq.ui import instance


@pytest.fixture(scope="session")
def app():
    return QApplication.instance() or QApplication([])


@pytest.fixture
def stubbed(monkeypatch, app, tmp_path):
    """`main` ohne Ereignisschleife und ohne echten Namensanspruch."""
    monkeypatch.setattr(QApplication, "exec", lambda self: 0)
    # Eine zweite QApplication liesse sich gar nicht bauen.
    monkeypatch.setattr(entry, "QApplication", lambda argv: app)
    monkeypatch.setattr(entry, "config_location", lambda: tmp_path / "config.json")
    monkeypatch.setattr(
        entry, "legacy_location", lambda: tmp_path / "alt" / "config.json"
    )
    monkeypatch.setattr(entry.sys, "argv", ["ProjectHQ.exe", "--no-boot"])

    servers = []
    # Vor dem Ersetzen festhalten: `entry.instance` ist dasselbe Modul, der
    # Stub riefe sonst sich selbst auf.
    real_listen = instance.listen

    def listen():
        server = real_listen(f"ProjectHQ-test-{uuid.uuid4().hex}")
        servers.append(server)
        return server

    monkeypatch.setattr(entry.instance, "listen", listen)
    yield tmp_path
    for server in servers:
        server.close()


@pytest.fixture
def taken(monkeypatch):
    """Es laeuft schon eine Instanz."""
    woken = []
    monkeypatch.setattr(entry.instance, "claim", lambda: None)
    monkeypatch.setattr(
        entry.instance, "wake_running_instance", lambda: woken.append(True) or True
    )
    return woken


@pytest.fixture
def free(monkeypatch):
    """Der Name ist frei."""
    monkeypatch.setattr(entry.instance, "claim", lambda: 4711)


# --- Der zweite Start ------------------------------------------------------


def test_a_second_start_wakes_the_first_and_stops(stubbed, taken, monkeypatch):
    built = []
    monkeypatch.setattr(entry, "MainWindow", lambda *a: built.append(a))

    assert entry.main() == 0
    assert taken == [True]
    assert built == [], "der zweite Start darf kein zweites Fenster bauen"


def test_a_second_start_stops_even_if_nobody_answers(stubbed, monkeypatch):
    """Antwortet die laufende Instanz nicht - sie startet noch, sie haengt -,
    ist das eigene Ende immer noch besser als ein zweiter Launcher."""
    monkeypatch.setattr(entry.instance, "claim", lambda: None)
    monkeypatch.setattr(entry.instance, "wake_running_instance", lambda: False)
    built = []
    monkeypatch.setattr(entry, "MainWindow", lambda *a: built.append(a))

    assert entry.main() == 0
    assert built == []


# --- Der erste Start -------------------------------------------------------


def test_the_first_start_shows_its_window(stubbed, free):
    assert entry.main() == 0
    titles = [w.windowTitle() for w in QApplication.topLevelWidgets()]
    assert "CODE/X HQ" in titles


def test_the_first_start_listens_for_later_ones(stubbed, free, monkeypatch):
    """Ohne das koennte ein spaeterer Start das Fenster nicht nach vorn holen."""
    listened = []
    original = entry.instance.listen
    monkeypatch.setattr(
        entry.instance, "listen", lambda: listened.append(True) or original()
    )

    entry.main()
    assert listened == [True]


def test_the_boot_screen_runs_without_no_boot(stubbed, free, monkeypatch):
    monkeypatch.setattr(entry.sys, "argv", ["ProjectHQ.exe"])
    entry.main()

    boot = getattr(QApplication.instance(), "boot_screen", None)
    assert boot is not None, "ohne Referenz raeumt Python den Schirm ab"
    boot.close()


# --- Die Einstellungen finden ----------------------------------------------


def test_settings_are_taken_over_from_the_old_location(stubbed, free):
    legacy = stubbed / "alt" / "config.json"
    legacy.parent.mkdir(parents=True)
    legacy.write_text(json.dumps({"console_style": "classic"}), encoding="utf-8")

    entry.main()

    taken_over = json.loads((stubbed / "config.json").read_text(encoding="utf-8"))
    assert taken_over["console_style"] == "classic"


def test_nothing_is_taken_over_when_there_is_nothing(stubbed, free):
    entry.main()
    assert not (stubbed / "config.json").exists()
