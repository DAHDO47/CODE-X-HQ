import json
from pathlib import Path

import pytest

from projecthq.config import (
    AGENT_LABELS,
    AGENT_MARKS,
    AGENT_NOTES,
    AGENTS,
    DEFAULT_ROOT,
    Config,
    adopt_legacy,
    config_location,
    resolve_agent,
)
from projecthq.theme import THEMES


def test_load_missing_file_uses_defaults(tmp_path):
    cfg = Config.load(tmp_path / "nope.json")
    assert cfg.projects_root == DEFAULT_ROOT
    assert cfg.favorites == []


def test_load_corrupt_file_uses_defaults(tmp_path):
    path = tmp_path / "config.json"
    path.write_text("{ not json", encoding="utf-8")
    cfg = Config.load(path)
    assert cfg.projects_root == DEFAULT_ROOT
    assert cfg.favorites == []


def test_save_then_load_roundtrip(tmp_path):
    path = tmp_path / "config.json"
    cfg = Config.load(path)
    cfg.projects_root = tmp_path / "projects"
    cfg.toggle_favorite("Gangland")
    cfg.save(path)

    again = Config.load(path)
    assert again.projects_root == tmp_path / "projects"
    assert again.is_favorite("Gangland") is True


def test_save_writes_readable_json(tmp_path):
    path = tmp_path / "config.json"
    cfg = Config.load(path)
    cfg.projects_root = tmp_path / "projects"
    cfg.save(path)
    data = json.loads(path.read_text(encoding="utf-8"))
    assert "projects_root" in data
    assert data["favorites"] == []


def test_rename_entry_moves_favorite(tmp_path):
    cfg = Config.load(tmp_path / "c.json")
    cfg.toggle_favorite("Alt")
    cfg.rename_entry("Alt", "Neu")
    assert cfg.is_favorite("Neu") is True
    assert cfg.is_favorite("Alt") is False


def test_rename_entry_without_existing_data_is_noop(tmp_path):
    cfg = Config.load(tmp_path / "c.json")
    cfg.rename_entry("Alt", "Neu")
    assert cfg.favorites == []


def test_toggle_favorite_returns_new_state(tmp_path):
    cfg = Config.load(tmp_path / "c.json")
    assert cfg.toggle_favorite("A") is True
    assert cfg.toggle_favorite("A") is False
    assert cfg.favorites == []


# --- Eigene Startbefehle gibt es nicht mehr -------------------------------


def test_save_no_longer_writes_a_commands_block(tmp_path):
    path = tmp_path / "c.json"
    Config().save(path)
    data = json.loads(path.read_text(encoding="utf-8"))
    assert "commands" not in data
    assert set(data) == {
        "projects_root",
        "favorites",
        "sort_key",
        "sort_desc",
        "console_style",
        "app_theme",
        "language",
        "last_agent",
        "last_shell",
        "project_agents",
        "project_started",
        "shutdown_at",
    }


def test_load_ignores_a_leftover_commands_block(tmp_path):
    """Eine config.json aus der Vorversion darf den Start nicht stoeren."""
    path = tmp_path / "c.json"
    path.write_text(
        json.dumps(
            {
                "projects_root": r"D:\Projekte",
                "commands": {"Alpha": "start.bat"},
                "favorites": ["Alpha"],
            }
        ),
        encoding="utf-8",
    )
    cfg = Config.load(path)
    assert cfg.projects_root == Path(r"D:\Projekte")
    assert cfg.favorites == ["Alpha"]
    assert not hasattr(cfg, "commands")


# --- Sortierung wird gemerkt ----------------------------------------------


def test_defaults_sort_by_modification_time_newest_first(tmp_path):
    cfg = Config.load(tmp_path / "nope.json")
    assert cfg.sort_key == "mtime"
    assert cfg.sort_desc is True


def test_sort_setting_survives_save_and_load(tmp_path):
    path = tmp_path / "config.json"
    cfg = Config.load(path)
    cfg.sort_key = "name"
    cfg.sort_desc = False
    cfg.save(path)

    again = Config.load(path)
    assert again.sort_key == "name"
    assert again.sort_desc is False


def test_load_rejects_an_unknown_sort_key(tmp_path):
    path = tmp_path / "c.json"
    path.write_text(
        json.dumps({"sort_key": "gibtsnicht", "sort_desc": False}), encoding="utf-8"
    )
    cfg = Config.load(path)
    assert cfg.sort_key == "mtime"
    assert cfg.sort_desc is True


def test_load_rejects_a_non_boolean_direction(tmp_path):
    path = tmp_path / "c.json"
    path.write_text(json.dumps({"sort_key": "kind", "sort_desc": "ja"}), encoding="utf-8")
    cfg = Config.load(path)
    assert cfg.sort_key == "kind"
    assert cfg.sort_desc is True


def test_old_config_without_sort_block_still_loads(tmp_path):
    path = tmp_path / "c.json"
    path.write_text(
        json.dumps({"projects_root": r"D:\Projekte", "favorites": []}), encoding="utf-8"
    )
    cfg = Config.load(path)
    assert cfg.sort_key == "mtime"
    assert cfg.sort_desc is True


# --- Konsolen-Design wird gemerkt -----------------------------------------


def test_defaults_to_the_crt_console(tmp_path):
    cfg = Config.load(tmp_path / "nope.json")
    assert cfg.console_style == "crt"


def test_console_style_survives_save_and_load(tmp_path):
    path = tmp_path / "config.json"
    cfg = Config.load(path)
    cfg.console_style = "classic"
    cfg.save(path)

    assert Config.load(path).console_style == "classic"


def test_load_rejects_an_unknown_console_style(tmp_path):
    path = tmp_path / "c.json"
    path.write_text(json.dumps({"console_style": "neon"}), encoding="utf-8")
    assert Config.load(path).console_style == "crt"


def test_old_config_without_console_style_still_loads(tmp_path):
    path = tmp_path / "c.json"
    path.write_text(
        json.dumps({"projects_root": r"D:\Projekte", "favorites": []}), encoding="utf-8"
    )
    cfg = Config.load(path)
    assert cfg.projects_root == Path(r"D:\Projekte")
    assert cfg.console_style == "crt"


# --- Design der Oberflaeche wird gemerkt ----------------------------------


def test_defaults_to_the_green_theme(tmp_path):
    cfg = Config.load(tmp_path / "nope.json")
    assert cfg.app_theme == "green"


def test_app_theme_survives_save_and_load(tmp_path):
    path = tmp_path / "config.json"
    cfg = Config.load(path)
    cfg.app_theme = "dos"
    cfg.save(path)

    assert Config.load(path).app_theme == "dos"


def test_load_rejects_an_unknown_app_theme(tmp_path):
    path = tmp_path / "c.json"
    path.write_text(json.dumps({"app_theme": "neon"}), encoding="utf-8")
    assert Config.load(path).app_theme == "green"


def test_old_config_without_app_theme_still_loads(tmp_path):
    path = tmp_path / "c.json"
    path.write_text(
        json.dumps({"projects_root": r"D:\Projekte", "favorites": []}), encoding="utf-8"
    )
    cfg = Config.load(path)
    assert cfg.projects_root == Path(r"D:\Projekte")
    assert cfg.app_theme == "green"


def test_all_four_themes_are_offered():
    assert set(THEMES) == {"green", "dos", "hacker", "gray"}


# --- Womit ein Projekt startet --------------------------------------------


def test_defaults_to_claude(tmp_path):
    assert Config.load(tmp_path / "nope.json").last_agent == "claude"


def test_the_chosen_agent_survives_save_and_load(tmp_path):
    path = tmp_path / "config.json"
    cfg = Config.load(path)
    cfg.last_agent = "codex"
    cfg.save(path)

    assert Config.load(path).last_agent == "codex"


def test_load_rejects_an_unknown_agent(tmp_path):
    path = tmp_path / "c.json"
    path.write_text(json.dumps({"last_agent": "eliza"}), encoding="utf-8")
    assert Config.load(path).last_agent == "claude"


def test_an_older_config_without_an_agent_still_loads(tmp_path):
    path = tmp_path / "c.json"
    path.write_text(
        json.dumps({"projects_root": r"D:\Projekte", "console_style": "classic"}),
        encoding="utf-8",
    )
    cfg = Config.load(path)
    assert cfg.last_agent == "claude"
    assert cfg.console_style == "classic"


def test_both_agents_are_offered():
    assert set(AGENTS) == {"claude", "codex"}


def test_resolve_agent_keeps_a_known_name():
    assert resolve_agent("codex") == "codex"
    assert resolve_agent("claude") == "claude"


def test_resolve_agent_falls_back_for_anything_unknown():
    """Damit niemand den tatsaechlich gemeinten Namen aus einem fertig
    gebauten Befehlsstring zurueckfischen muss."""
    for unknown in ("eliza", "", None, "CLAUDE"):
        assert resolve_agent(unknown) == "claude"


def test_every_agent_has_a_label_and_a_note():
    """Ein dritter Agent soll an genau einer Stelle entstehen."""
    for agent in AGENTS:
        assert AGENT_LABELS[agent]
        assert AGENT_NOTES[agent]
    assert set(AGENT_LABELS) == set(AGENTS)
    assert set(AGENT_NOTES) == set(AGENTS)


# --- Ein abgebrochenes Speichern zerstoert nichts -------------------------


def test_a_failed_save_leaves_the_previous_file_intact(tmp_path, monkeypatch):
    """Geschrieben wird daneben und dann umgelegt.

    Bricht das Schreiben mittendrin ab - volle Platte, Absturz -, stuende
    sonst eine halbe Datei am Ziel. `load` faengt das zwar ab, aber still:
    alle Einstellungen waeren auf Vorgabe zurueck.
    """
    path = tmp_path / "config.json"
    before = Config()
    before.console_style = "classic"
    before.save(path)

    write_text = Path.write_text

    def half_then_fail(self, data, *args, **kwargs):
        write_text(self, data[: len(data) // 2], *args, **kwargs)
        raise OSError("Abbruch mitten im Schreiben")

    monkeypatch.setattr(Path, "write_text", half_then_fail)
    after = Config()
    after.console_style = "crt"
    with pytest.raises(OSError):
        after.save(path)

    monkeypatch.undo()
    assert Config.load(path).console_style == "classic"


def test_a_failed_save_leaves_no_scraps_behind(tmp_path, monkeypatch):
    path = tmp_path / "config.json"
    Config().save(path)

    def fail(self, data, *args, **kwargs):
        raise OSError("Platte voll")

    monkeypatch.setattr(Path, "write_text", fail)
    with pytest.raises(OSError):
        Config().save(path)

    monkeypatch.undo()
    assert [p.name for p in tmp_path.iterdir()] == ["config.json"]


# --- Wo die Datei liegt ---------------------------------------------------
#
# Sie darf nicht neben der .exe liegen: `build.ps1` laesst PyInstaller mit
# `--noconfirm` laufen, und das raeumt `dist\ProjectHQ` vor jedem Build leer.


def test_config_lies_in_appdata(tmp_path, monkeypatch):
    monkeypatch.setenv("APPDATA", str(tmp_path))
    assert config_location() == tmp_path / "ProjectHQ" / "config.json"


def test_config_falls_back_to_the_home_folder_without_appdata(tmp_path, monkeypatch):
    monkeypatch.delenv("APPDATA", raising=False)
    monkeypatch.setattr(Path, "home", classmethod(lambda cls: tmp_path))
    assert config_location() == tmp_path / ".projecthq" / "config.json"


def test_adopt_legacy_takes_over_the_old_file(tmp_path):
    legacy = tmp_path / "alt" / "config.json"
    legacy.parent.mkdir()
    legacy.write_text(json.dumps({"console_style": "classic"}), encoding="utf-8")
    target = tmp_path / "neu" / "config.json"

    assert adopt_legacy(target, legacy) is True
    assert Config.load(target).console_style == "classic"


def test_adopt_legacy_leaves_an_existing_file_alone(tmp_path):
    legacy = tmp_path / "alt" / "config.json"
    legacy.parent.mkdir()
    legacy.write_text(json.dumps({"console_style": "classic"}), encoding="utf-8")
    target = tmp_path / "neu" / "config.json"
    target.parent.mkdir()
    target.write_text(json.dumps({"console_style": "crt"}), encoding="utf-8")

    assert adopt_legacy(target, legacy) is False
    assert Config.load(target).console_style == "crt"


def test_adopt_legacy_without_an_old_file_does_nothing(tmp_path):
    target = tmp_path / "neu" / "config.json"
    assert adopt_legacy(target, tmp_path / "gibtsnicht.json") is False
    assert not target.exists()


# --- Womit ein Projekt zuletzt gestartet wurde ----------------------------


def test_a_fresh_config_remembers_no_agent_for_any_project(tmp_path):
    cfg = Config.load(tmp_path / "nope.json")
    assert cfg.project_agents == {}
    assert cfg.agent_of("Gangland") == ""


def test_the_agent_of_a_project_survives_save_and_load(tmp_path):
    path = tmp_path / "config.json"
    cfg = Config.load(path)
    cfg.remember_agent("Gangland", "codex")
    cfg.save(path)

    assert Config.load(path).agent_of("Gangland") == "codex"


def test_remembering_again_overwrites_the_previous_agent(tmp_path):
    cfg = Config()
    cfg.remember_agent("Gangland", "codex")
    cfg.remember_agent("Gangland", "claude")
    assert cfg.agent_of("Gangland") == "claude"


def test_load_drops_a_project_with_an_unknown_agent(tmp_path):
    """Dieselbe Regel wie ueberall: eine von Hand verstellte Datei soll den
    Start nicht kippen, sondern den unbrauchbaren Eintrag verlieren."""
    path = tmp_path / "c.json"
    path.write_text(
        json.dumps({"project_agents": {"Gangland": "eliza", "Tarkov": "codex"}}),
        encoding="utf-8",
    )
    cfg = Config.load(path)
    assert cfg.agent_of("Gangland") == ""
    assert cfg.agent_of("Tarkov") == "codex"


def test_load_survives_a_project_agents_block_that_is_not_a_table(tmp_path):
    path = tmp_path / "c.json"
    path.write_text(json.dumps({"project_agents": ["Gangland"]}), encoding="utf-8")
    assert Config.load(path).project_agents == {}


def test_load_drops_entries_that_are_not_text(tmp_path):
    path = tmp_path / "c.json"
    path.write_text(
        json.dumps({"project_agents": {"Gangland": 7, "Tarkov": None}}),
        encoding="utf-8",
    )
    assert Config.load(path).project_agents == {}


def test_an_older_config_without_the_block_still_loads(tmp_path):
    path = tmp_path / "c.json"
    path.write_text(json.dumps({"last_agent": "codex"}), encoding="utf-8")
    cfg = Config.load(path)
    assert cfg.project_agents == {}
    assert cfg.last_agent == "codex"


def test_renaming_a_project_carries_its_agent_along(tmp_path):
    cfg = Config()
    cfg.remember_agent("Alpha", "codex")
    cfg.rename_entry("Alpha", "Beta")
    assert cfg.agent_of("Beta") == "codex"
    assert cfg.agent_of("Alpha") == ""


def test_renaming_a_project_without_an_agent_changes_nothing(tmp_path):
    cfg = Config()
    cfg.rename_entry("Alpha", "Beta")
    assert cfg.project_agents == {}


def test_forget_removes_favorite_and_agent_together(tmp_path):
    """Was geloescht wurde, soll in der Datei nichts mehr hinterlassen."""
    cfg = Config()
    cfg.toggle_favorite("Alpha")
    cfg.remember_agent("Alpha", "codex")

    cfg.forget("Alpha")

    assert cfg.is_favorite("Alpha") is False
    assert cfg.agent_of("Alpha") == ""


def test_forget_is_quiet_about_a_project_it_never_saw(tmp_path):
    cfg = Config()
    cfg.forget("Alpha")
    assert cfg.favorites == []
    assert cfg.project_agents == {}


# --- Wann ein Projekt zuletzt ueber HQ gestartet wurde --------------------


def test_a_fresh_config_remembers_no_start_for_any_project(tmp_path):
    cfg = Config.load(tmp_path / "nope.json")
    assert cfg.project_started == {}
    assert cfg.started_of("Gangland") == 0.0


def test_the_start_of_a_project_survives_save_and_load(tmp_path):
    path = tmp_path / "config.json"
    cfg = Config.load(path)
    cfg.remember_started("Gangland", 1234.5)
    cfg.save(path)

    assert Config.load(path).started_of("Gangland") == 1234.5


def test_remembering_a_start_again_overwrites_the_previous_one(tmp_path):
    cfg = Config()
    cfg.remember_started("Gangland", 1000.0)
    cfg.remember_started("Gangland", 2000.0)
    assert cfg.started_of("Gangland") == 2000.0


def test_load_survives_a_project_started_block_that_is_not_a_table(tmp_path):
    path = tmp_path / "c.json"
    path.write_text(json.dumps({"project_started": ["Gangland"]}), encoding="utf-8")
    assert Config.load(path).project_started == {}


def test_load_drops_start_entries_that_are_not_a_number(tmp_path):
    path = tmp_path / "c.json"
    path.write_text(
        json.dumps({"project_started": {"Gangland": "gestern", "Tarkov": 42}}),
        encoding="utf-8",
    )
    cfg = Config.load(path)
    assert cfg.started_of("Gangland") == 0.0
    assert cfg.started_of("Tarkov") == 42.0


def test_an_older_config_without_the_started_block_still_loads(tmp_path):
    path = tmp_path / "c.json"
    path.write_text(json.dumps({"last_agent": "codex"}), encoding="utf-8")
    cfg = Config.load(path)
    assert cfg.project_started == {}
    assert cfg.last_agent == "codex"


def test_renaming_a_project_carries_its_start_time_along(tmp_path):
    cfg = Config()
    cfg.remember_started("Alpha", 1000.0)
    cfg.rename_entry("Alpha", "Beta")
    assert cfg.started_of("Beta") == 1000.0
    assert cfg.started_of("Alpha") == 0.0


def test_forget_removes_the_start_time_too(tmp_path):
    cfg = Config()
    cfg.remember_started("Alpha", 1000.0)
    cfg.forget("Alpha")
    assert cfg.started_of("Alpha") == 0.0


# --- Automatischer Shutdown -------------------------------------------


def test_a_fresh_config_has_no_shutdown_scheduled(tmp_path):
    cfg = Config.load(tmp_path / "nope.json")
    assert cfg.shutdown_at == 0.0


def test_shutdown_at_survives_save_and_load(tmp_path):
    path = tmp_path / "config.json"
    cfg = Config.load(path)
    cfg.shutdown_at = 1234.5
    cfg.save(path)

    assert Config.load(path).shutdown_at == 1234.5


def test_load_rejects_a_non_numeric_shutdown_at(tmp_path):
    path = tmp_path / "c.json"
    path.write_text(json.dumps({"shutdown_at": "morgen"}), encoding="utf-8")
    assert Config.load(path).shutdown_at == 0.0


def test_an_older_config_without_shutdown_at_still_loads(tmp_path):
    path = tmp_path / "c.json"
    path.write_text(json.dumps({"last_agent": "codex"}), encoding="utf-8")
    cfg = Config.load(path)
    assert cfg.shutdown_at == 0.0
    assert cfg.last_agent == "codex"


def test_every_agent_has_a_mark_and_all_marks_differ():
    """Ein dritter Agent entsteht an genau einer Stelle - dann faellt hier
    auf, wenn sein Symbol vergessen wurde."""
    assert set(AGENT_MARKS) == set(AGENTS)
    assert len(set(AGENT_MARKS.values())) == len(AGENTS)


# --- Welche Shell ---------------------------------------------------------


def test_defaults_to_cmd(tmp_path):
    assert Config.load(tmp_path / "nope.json").last_shell == "cmd"


def test_the_chosen_shell_survives_save_and_load(tmp_path):
    path = tmp_path / "config.json"
    cfg = Config.load(path)
    cfg.last_shell = "powershell"
    cfg.save(path)
    assert Config.load(path).last_shell == "powershell"


def test_load_rejects_an_unknown_shell(tmp_path):
    path = tmp_path / "c.json"
    path.write_text(json.dumps({"last_shell": "bash"}), encoding="utf-8")
    assert Config.load(path).last_shell == "cmd"


# --- Sprache --------------------------------------------------------------


def test_defaults_to_german(tmp_path):
    assert Config.load(tmp_path / "nope.json").language == "de"


def test_the_chosen_language_survives_save_and_load(tmp_path):
    path = tmp_path / "config.json"
    cfg = Config.load(path)
    cfg.language = "tr"
    cfg.save(path)
    assert Config.load(path).language == "tr"


def test_load_rejects_an_unknown_language(tmp_path):
    path = tmp_path / "c.json"
    path.write_text(json.dumps({"language": "klingon"}), encoding="utf-8")
    assert Config.load(path).language == "de"
