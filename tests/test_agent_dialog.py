"""Tests fuer den Startdialog: womit soll das Projekt laufen?

Der Dialog fragt bei jedem Start. Damit das nicht bremst, steht die
zuletzt getroffene Wahl schon bereit - Enter startet also sofort.
"""

from __future__ import annotations

import pytest
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QDialog

from projecthq.scanner import Project
from projecthq.ui import dialogs
from projecthq.ui.dialogs import _AgentDialog


@pytest.fixture(scope="session")
def app():
    return QApplication.instance() or QApplication([])


@pytest.fixture
def project(tmp_path) -> Project:
    path = tmp_path / "Tarkov"
    path.mkdir()
    return Project(name="Tarkov", path=path, kind="py", created=0.0, mtime=0.0)


def test_both_agents_are_offered(app, project):
    dialog = _AgentDialog(None, project, "claude")
    assert set(dialog.agent_buttons) == {"claude", "codex"}


def test_the_last_choice_is_preselected(app, project):
    assert _AgentDialog(None, project, "codex").selected_agent() == "codex"
    assert _AgentDialog(None, project, "claude").selected_agent() == "claude"


def test_an_unknown_last_choice_shows_the_default(app, project):
    """Eine von Hand verstellte config.json darf den Dialog nicht kippen."""
    assert _AgentDialog(None, project, "eliza").selected_agent() == "claude"


def test_choosing_the_other_agent_is_what_comes_back(app, project):
    dialog = _AgentDialog(None, project, "claude")
    dialog.agent_buttons["codex"].setChecked(True)
    assert dialog.selected_agent() == "codex"


def test_the_dialog_names_the_project(app, project):
    """Sonst weiss man beim Startdialog nicht mehr, was man gewaehlt hat."""
    dialog = _AgentDialog(None, project, "claude")
    texts = [label.text() for label in dialog.findChildren(type(dialog.hint))]
    assert any("Tarkov" in text for text in texts)


def test_start_is_the_default_button_so_enter_starts(app, project):
    """Der Dialog steht auf dem haeufigsten Weg des Programms: Enter muss
    reichen, sonst kostet jeder Start einen Klick mehr."""
    dialog = _AgentDialog(None, project, "claude")
    assert dialog.start_button.isDefault()


# --- Der Weg durch ask_agent ----------------------------------------------


def test_ask_agent_returns_the_choice(app, project, monkeypatch):
    def accept(self):
        self.agent_buttons["codex"].setChecked(True)
        return QDialog.Accepted

    monkeypatch.setattr(_AgentDialog, "exec", accept)
    assert dialogs.ask_agent(None, project, "claude").agent == "codex"


def test_cancelling_returns_nothing(app, project, monkeypatch):
    monkeypatch.setattr(_AgentDialog, "exec", lambda self: QDialog.Rejected)
    assert dialogs.ask_agent(None, project, "claude") is None


# --- Als Administrator starten --------------------------------------------


def test_the_dialog_offers_an_admin_option(app, project):
    assert _AgentDialog(None, project, "claude").admin_box is not None


def test_admin_is_off_at_every_start(app, project):
    """Bewusst nicht gemerkt: ein stehengebliebenes Haekchen hiesse, dass
    jeder spaetere Start still einen UAC-Dialog aufmacht."""
    assert _AgentDialog(None, project, "claude").admin_box.isChecked() is False


def test_ask_agent_reports_a_plain_start(app, project, monkeypatch):
    monkeypatch.setattr(_AgentDialog, "exec", lambda self: QDialog.Accepted)
    assert dialogs.ask_agent(None, project, "claude") == ("claude", False, False, "cmd")


def test_ask_agent_reports_the_ticked_admin_box(app, project, monkeypatch):
    def accept(self):
        self.admin_box.setChecked(True)
        return QDialog.Accepted

    monkeypatch.setattr(_AgentDialog, "exec", accept)
    assert dialogs.ask_agent(None, project, "codex") == ("codex", True, False, "cmd")


def test_the_choice_can_be_read_by_name(app, project, monkeypatch):
    """`choice.agent` und `choice.admin` lesen sich besser als [0] und [1]."""
    monkeypatch.setattr(_AgentDialog, "exec", lambda self: QDialog.Accepted)
    choice = dialogs.ask_agent(None, project, "codex")
    assert (choice.agent, choice.admin) == ("codex", False)


# --- Ohne Rueckfragen -----------------------------------------------------


def test_skip_permissions_is_off_at_every_start(app, project):
    """Wie das Admin-Haekchen nie gemerkt: sonst liefe jeder spaetere
    Start still ohne Rueckfragen."""
    assert _AgentDialog(None, project, "claude").skip_box.isChecked() is False


def test_skip_permissions_is_offered_for_both_agents(app, project):
    """Codex kann es auch - nur mit anderen Schaltern."""
    dialog = _AgentDialog(None, project, "claude")
    assert dialog.skip_box.isEnabled()
    dialog.agent_buttons["codex"].setChecked(True)
    assert dialog.skip_box.isEnabled()


def test_the_skip_box_names_the_flags_of_the_chosen_agent(app, project):
    """Man soll sehen, was man erlaubt."""
    dialog = _AgentDialog(None, project, "claude")
    assert "--dangerously-skip-permissions" in dialog.skip_box.text()
    dialog.agent_buttons["codex"].setChecked(True)
    assert (
        "--sandbox danger-full-access --ask-for-approval never"
        in dialog.skip_box.text()
    )


def test_ask_agent_reports_the_ticked_skip_box(app, project, monkeypatch):
    def accept(self):
        self.skip_box.setChecked(True)
        return QDialog.Accepted

    monkeypatch.setattr(_AgentDialog, "exec", accept)
    assert dialogs.ask_agent(None, project, "claude") == ("claude", False, True, "cmd")


# --- cmd oder PowerShell --------------------------------------------------


def test_both_shells_are_offered(app, project):
    assert set(_AgentDialog(None, project, "claude").shell_buttons) == {
        "cmd",
        "powershell",
    }


def test_the_last_shell_is_preselected(app, project):
    dialog = _AgentDialog(None, project, "claude", "powershell")
    assert dialog.selected_shell() == "powershell"


def test_an_unknown_shell_shows_the_default(app, project):
    assert _AgentDialog(None, project, "claude", "bash").selected_shell() == "cmd"


def test_ask_agent_reports_the_chosen_shell(app, project, monkeypatch):
    def accept(self):
        self.shell_buttons["powershell"].setChecked(True)
        return QDialog.Accepted

    monkeypatch.setattr(_AgentDialog, "exec", accept)
    assert dialogs.ask_agent(None, project, "codex").shell == "powershell"
