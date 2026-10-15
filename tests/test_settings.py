"""Tests fuer den Einstellungsdialog.

Der Dialog aendert die `Config` erst beim OK. Was er anzeigt und was er
zurueckschreibt, ist ohne sichtbaren Bildschirm pruefbar; nur der
Ordnerdialog von Windows wird ersetzt.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from PySide6.QtWidgets import QApplication

from projecthq.config import Config
from projecthq.ui import dialogs
from projecthq.ui.dialogs import _SettingsDialog


@pytest.fixture(scope="session")
def app():
    return QApplication.instance() or QApplication([])


@pytest.fixture
def config(tmp_path) -> Config:
    cfg = Config()
    cfg.projects_root = tmp_path / "projekte"
    return cfg


def test_dialog_starts_on_the_configured_style(app, config):
    config.console_style = "classic"
    assert _SettingsDialog(None, config).selected_style() == "classic"


def test_choosing_the_other_style_lands_in_the_config(app, config):
    config.console_style = "classic"
    dialog = _SettingsDialog(None, config)
    dialog.style_buttons["crt"].setChecked(True)

    assert dialog.apply_to(config) is True
    assert config.console_style == "crt"


def test_ok_without_a_change_reports_nothing_changed(app, config):
    dialog = _SettingsDialog(None, config)
    assert dialog.apply_to(config) is False


def test_dialog_shows_the_configured_project_folder(app, config):
    assert _SettingsDialog(None, config).selected_root() == config.projects_root


def test_a_newly_chosen_folder_lands_in_the_config(app, config, tmp_path, monkeypatch):
    chosen = tmp_path / "woanders"
    monkeypatch.setattr(
        dialogs.QFileDialog, "getExistingDirectory", lambda *a, **k: str(chosen)
    )
    dialog = _SettingsDialog(None, config)
    dialog.choose_root()

    assert dialog.apply_to(config) is True
    assert config.projects_root == chosen


def test_cancelling_the_folder_dialog_keeps_the_old_one(app, config, monkeypatch):
    monkeypatch.setattr(
        dialogs.QFileDialog, "getExistingDirectory", lambda *a, **k: ""
    )
    dialog = _SettingsDialog(None, config)
    dialog.choose_root()

    assert dialog.selected_root() == config.projects_root
    assert dialog.apply_to(config) is False


def test_an_unknown_style_in_the_config_shows_the_default(app, config):
    """Eine von Hand verstellte config.json darf den Dialog nicht kippen."""
    config.console_style = "neon"
    assert _SettingsDialog(None, config).selected_style() == "crt"


def test_both_styles_are_offered(app, config):
    dialog = _SettingsDialog(None, config)
    assert set(dialog.style_buttons) == {"crt", "classic"}


def test_dialog_starts_on_the_configured_theme(app, config):
    config.app_theme = "dos"
    assert _SettingsDialog(None, config).selected_theme() == "dos"


def test_choosing_another_theme_lands_in_the_config(app, config):
    dialog = _SettingsDialog(None, config)
    dialog.theme_buttons["hacker"].setChecked(True)

    assert dialog.apply_to(config) is True
    assert config.app_theme == "hacker"


def test_an_unknown_theme_in_the_config_shows_the_default(app, config):
    """Eine von Hand verstellte config.json darf den Dialog nicht kippen."""
    config.app_theme = "neon"
    assert _SettingsDialog(None, config).selected_theme() == "green"


def test_all_three_themes_are_offered_in_the_dialog(app, config):
    dialog = _SettingsDialog(None, config)
    assert set(dialog.theme_buttons) == {"green", "dos", "hacker"}


def test_the_shown_folder_is_the_one_that_gets_saved(app, config, tmp_path, monkeypatch):
    """Was im Dialog steht, ist auch das, was beim OK gespeichert wird."""
    chosen = tmp_path / "neu"
    monkeypatch.setattr(
        dialogs.QFileDialog, "getExistingDirectory", lambda *a, **k: str(chosen)
    )
    dialog = _SettingsDialog(None, config)
    dialog.choose_root()
    assert dialog.selected_root() == Path(chosen)


# --- Sprache --------------------------------------------------------------


def test_all_languages_are_offered(app, config):
    dialog = _SettingsDialog(None, config)
    offered = [
        dialog.language_combo.itemData(i) for i in range(dialog.language_combo.count())
    ]
    assert offered == ["de", "en", "bhs", "tr", "es"]


def test_dialog_starts_on_the_configured_language(app, config):
    config.language = "es"
    assert _SettingsDialog(None, config).selected_language() == "es"


def test_choosing_another_language_lands_in_the_config(app, config):
    dialog = _SettingsDialog(None, config)
    dialog.language_combo.setCurrentIndex(1)
    assert dialog.apply_to(config) is True
    assert config.language == "en"
