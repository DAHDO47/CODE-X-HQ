import os
import time
from pathlib import Path

import pytest

from projecthq import runner, theme
from projecthq.config import Config
from projecthq.scanner import NOTE_NAME, Project, scan


def project_at(tmp_path: Path, name: str) -> Project:
    (tmp_path / name).mkdir(parents=True, exist_ok=True)
    return [p for p in scan(tmp_path) if p.name == name][0]


def test_validate_name_rejects_empty(tmp_path):
    p = project_at(tmp_path, "Alpha")
    with pytest.raises(runner.RunnerError):
        runner.validate_name("   ", p.path.parent, p.path)


@pytest.mark.parametrize(
    "bad", ["a<b", "a>b", "a:b", 'a"b', "a/b", "a\\b", "a|b", "a?b", "a*b"]
)
def test_validate_name_rejects_forbidden_characters(tmp_path, bad):
    p = project_at(tmp_path, "Alpha")
    with pytest.raises(runner.RunnerError):
        runner.validate_name(bad, p.path.parent, p.path)


@pytest.mark.parametrize("bad", ["CON", "con", "PRN", "AUX", "NUL", "COM1", "LPT9"])
def test_validate_name_rejects_reserved_device_names(tmp_path, bad):
    p = project_at(tmp_path, "Alpha")
    with pytest.raises(runner.RunnerError):
        runner.validate_name(bad, p.path.parent, p.path)


def test_validate_name_rejects_trailing_dot_or_space(tmp_path):
    p = project_at(tmp_path, "Alpha")
    with pytest.raises(runner.RunnerError):
        runner.validate_name("Beta.", p.path.parent, p.path)


def test_validate_name_rejects_existing_sibling(tmp_path):
    (tmp_path / "Beta").mkdir()
    p = project_at(tmp_path, "Alpha")
    with pytest.raises(runner.RunnerError):
        runner.validate_name("Beta", p.path.parent, p.path)


def test_validate_name_allows_same_folder(tmp_path):
    p = project_at(tmp_path, "Alpha")
    runner.validate_name("Alpha", p.path.parent, p.path)


def test_rename_moves_folder(tmp_path):
    p = project_at(tmp_path, "Alpha")
    new_path = runner.rename(p, "Beta", Config())
    assert new_path == tmp_path / "Beta"
    assert new_path.is_dir()
    assert not (tmp_path / "Alpha").exists()


def test_rename_updates_project_object(tmp_path):
    p = project_at(tmp_path, "Alpha")
    runner.rename(p, "Beta", Config())
    assert p.name == "Beta"
    assert p.path == tmp_path / "Beta"


def test_rename_moves_favorite_entry(tmp_path):
    p = project_at(tmp_path, "Alpha")
    cfg = Config()
    cfg.toggle_favorite("Alpha")
    runner.rename(p, "Beta", cfg)
    assert cfg.is_favorite("Beta") is True
    assert cfg.is_favorite("Alpha") is False


def test_rename_strips_surrounding_whitespace(tmp_path):
    p = project_at(tmp_path, "Alpha")
    new_path = runner.rename(p, "  Beta  ", Config())
    assert new_path.name == "Beta"


def test_delete_uses_trash_and_clears_favorite(tmp_path, monkeypatch):
    trashed = []
    monkeypatch.setattr(runner, "send_to_trash", lambda path: trashed.append(Path(path)))
    p = project_at(tmp_path, "Alpha")
    cfg = Config()
    cfg.toggle_favorite("Alpha")

    runner.delete(p, cfg)

    assert trashed == [tmp_path / "Alpha"]
    assert cfg.is_favorite("Alpha") is False


def test_delete_missing_folder_raises(tmp_path, monkeypatch):
    monkeypatch.setattr(runner, "send_to_trash", lambda path: None)
    p = project_at(tmp_path, "Alpha")
    (tmp_path / "Alpha").rmdir()
    with pytest.raises(runner.RunnerError):
        runner.delete(p, Config())


def test_open_terminal_opens_a_plain_console(tmp_path, monkeypatch):
    calls = []
    monkeypatch.setattr(runner, "_spawn", lambda args, cwd: calls.append(args))
    p = project_at(tmp_path, "Alpha")
    runner.open_terminal(p, "classic")
    assert calls == [["cmd"]]


def test_open_terminal_never_hands_the_prologue_to_windows_terminal(
    tmp_path, monkeypatch
):
    """Regression: mit `wt` tat F4 im CRT-Design gar nichts.

    Windows Terminal parst die Kommandozeile selbst und kommt mit den
    ESC-Sequenzen des Vorspanns nicht zurecht. Gemessen: ein schlichter
    Befehl und eine &-Kette gehen durch, der Vorspann nicht - es lief dann
    nichts, und es ging nicht einmal ein Fenster auf.
    """
    monkeypatch.setattr(runner.shutil, "which", lambda name: r"C:\wt.exe")
    calls = []
    monkeypatch.setattr(runner, "_spawn", lambda args, cwd: calls.append(args))
    p = project_at(tmp_path, "Alpha")
    runner.open_terminal(p, "crt")

    assert calls[0][0] == "cmd"
    assert "wt" not in calls[0]


def test_the_terminal_looks_like_a_started_project(tmp_path, monkeypatch):
    """Beide oeffnen dieselbe Konsole - nur laeuft bei F4 kein Agent darin."""
    calls = []
    monkeypatch.setattr(runner, "_spawn", lambda args, cwd: calls.append(args))
    monkeypatch.setattr(runner.shutil, "which", lambda name: rf"C:\{name}.cmd")
    p = project_at(tmp_path, "Alpha")

    runner.start(p, "claude", "crt")
    runner.open_terminal(p, "crt")
    started, terminal = calls

    assert started[:2] == terminal[:2] == ["cmd", "/K"]
    assert started[2] == f"{terminal[2]}&claude"


def test_open_vscode_without_code_raises(tmp_path, monkeypatch):
    monkeypatch.setattr(runner.shutil, "which", lambda name: None)
    p = project_at(tmp_path, "Alpha")
    with pytest.raises(runner.RunnerError):
        runner.open_vscode(p)


def test_folder_size_sums_files(tmp_path):
    root = tmp_path / "Alpha"
    (root / "sub").mkdir(parents=True)
    (root / "a.txt").write_bytes(b"x" * 100)
    (root / "sub" / "b.txt").write_bytes(b"y" * 50)
    assert runner.folder_size(root) == (150, True)


# --- Die Groesse darf die Oberflaeche nicht anhalten ----------------------
#
# Der Loeschen-Dialog zeigt die Ordnergroesse und rechnet sie im
# Oberflaechen-Thread aus. Bei einem Projekt mit node_modules stuende das
# Fenster sonst sekundenlang, bevor ueberhaupt etwas erscheint.


def many_files(tmp_path: Path, count: int) -> Path:
    root = tmp_path / "Viel"
    root.mkdir()
    for index in range(count):
        (root / f"{index}.txt").write_bytes(b"x" * 10)
    return root


def test_folder_size_stops_after_the_file_budget(tmp_path):
    root = many_files(tmp_path, 20)
    total, complete = runner.folder_size(root, file_budget=5)
    assert complete is False
    assert 0 < total < 200


def test_folder_size_stops_after_the_time_budget(tmp_path):
    root = many_files(tmp_path, 20)
    total, complete = runner.folder_size(root, time_budget=0)
    assert complete is False
    assert total < 200


def test_size_label_reads_plainly_when_the_count_was_complete(tmp_path):
    root = many_files(tmp_path, 3)
    assert runner.size_label(root) == "30 B"


def test_size_label_marks_an_interrupted_count_as_a_lower_bound(tmp_path):
    root = many_files(tmp_path, 20)
    assert runner.size_label(root, file_budget=5).startswith("> ")


def test_human_size_formats():
    assert runner.human_size(0) == "0 B"
    assert runner.human_size(1023) == "1023 B"
    assert runner.human_size(1024) == "1.0 KB"
    assert runner.human_size(1024 * 1024 * 3) == "3.0 MB"


# --- Start: immer cmd + claude im Projektordner ---------------------------


@pytest.fixture
def agents_in_path(monkeypatch):
    """Tut so, als laegen beide Agenten im PATH.

    Ohne das haenge jeder Starttest davon ab, was auf dem Rechner, der ihn
    ausfuehrt, gerade installiert ist.
    """
    monkeypatch.setattr(
        runner.shutil,
        "which",
        lambda name: rf"C:\{name}.cmd" if name in ("claude", "codex") else None,
    )


def test_start_opens_cmd_with_claude_in_project_directory(
    tmp_path, monkeypatch, agents_in_path
):
    calls = []
    monkeypatch.setattr(runner, "_spawn", lambda args, cwd: calls.append((args, cwd)))
    p = project_at(tmp_path, "Alpha")
    runner.start(p, "claude", "classic")
    assert calls == [(["cmd", "/K", "claude"], p.path)]


def test_start_opens_cmd_with_codex_when_asked(tmp_path, monkeypatch, agents_in_path):
    calls = []
    monkeypatch.setattr(runner, "_spawn", lambda args, cwd: calls.append((args, cwd)))
    p = project_at(tmp_path, "Alpha")
    runner.start(p, "codex", "classic")
    assert calls == [(["cmd", "/K", "codex"], p.path)]


def test_both_agents_get_the_crt_prologue(tmp_path):
    """Die Konsole faerbt sich fuer beide gleich - der Agent aendert nur,
    was darin laeuft."""
    for agent in ("claude", "codex"):
        command = runner.agent_command(agent, "crt")
        assert command[:2] == ["cmd", "/K"]
        assert command[2].startswith(runner.CRT_PROLOG)
        assert command[2].endswith(f"&{agent}")


def test_an_unknown_agent_falls_back_to_the_default(tmp_path):
    """Steht in der config.json etwas Unbekanntes, soll der Start nicht
    kippen - dieselbe Regel wie beim Konsolen-Design."""
    assert runner.agent_command("eliza", "classic") == ["cmd", "/K", "claude"]


def test_start_is_the_same_for_every_project_type(
    tmp_path, monkeypatch, agents_in_path
):
    """Weder eine start.bat noch eine package.json aendern den Startbefehl."""
    calls = []
    monkeypatch.setattr(runner, "_spawn", lambda args, cwd: calls.append(args))
    bat = project_at(tmp_path, "MitBat")
    (bat.path / "start.bat").write_text("echo x", encoding="utf-8")
    node = project_at(tmp_path, "MitNode")
    (node.path / "package.json").write_text('{"scripts":{"dev":"x"}}', encoding="utf-8")
    runner.start(bat, "claude", "classic")
    runner.start(node, "claude", "classic")
    assert calls == [["cmd", "/K", "claude"], ["cmd", "/K", "claude"]]


def test_start_missing_folder_raises(tmp_path, monkeypatch, agents_in_path):
    monkeypatch.setattr(runner, "_spawn", lambda args, cwd: None)
    p = project_at(tmp_path, "Weg")
    p.path.rmdir()
    with pytest.raises(runner.RunnerError):
        runner.start(p)


def test_start_without_the_chosen_agent_in_the_path_says_so(tmp_path, monkeypatch):
    """Sonst geht eine Konsole auf, in der Windows meldet, der Befehl sei
    falsch geschrieben - und die bleibt wegen /K auch noch stehen."""
    monkeypatch.setattr(runner.shutil, "which", lambda name: None)
    monkeypatch.setattr(runner, "_spawn", lambda args, cwd: None)
    p = project_at(tmp_path, "Alpha")

    for agent in ("claude", "codex"):
        with pytest.raises(runner.RunnerError) as error:
            runner.start(p, agent)
        assert agent in str(error.value).lower()


def test_start_names_the_missing_agent_not_the_other_one(tmp_path, monkeypatch):
    """Ist Claude da und Codex nicht, muss die Meldung von Codex sprechen."""
    monkeypatch.setattr(
        runner.shutil, "which", lambda name: r"C:\claude.cmd" if name == "claude" else None
    )
    monkeypatch.setattr(runner, "_spawn", lambda args, cwd: None)
    p = project_at(tmp_path, "Alpha")

    with pytest.raises(runner.RunnerError) as error:
        runner.start(p, "codex")
    assert "codex" in str(error.value).lower()


# --- Fehlgeschlagene Starts bleiben nicht stumm ---------------------------


def raise_os_error(*args, **kwargs):
    raise OSError(2, "Das System kann die angegebene Datei nicht finden")


def test_spawn_reports_a_failed_start_as_runner_error(tmp_path, monkeypatch):
    """Der OSError schluege sonst bis in den Qt-Slot durch. Die .exe laeuft
    ohne Konsole, in der ein Traceback landen koennte: der Knopf taete
    kommentarlos nichts."""
    monkeypatch.setattr(runner.subprocess, "Popen", raise_os_error)
    with pytest.raises(runner.RunnerError) as error:
        runner._spawn(["gibtsnicht.exe"], tmp_path)
    assert "nicht finden" in str(error.value)


def test_open_explorer_reports_a_failed_start_as_runner_error(tmp_path, monkeypatch):
    monkeypatch.setattr(runner.os, "startfile", raise_os_error)
    p = project_at(tmp_path, "Alpha")
    with pytest.raises(runner.RunnerError):
        runner.open_explorer(p)


def test_spawn_does_not_build_a_shell_string(tmp_path, monkeypatch):
    """Regression: 'cmd /K "..."' mit shell=True zerbrach an Pfaden mit
    Leerzeichen, weil cmd die aeusseren Anfuehrungszeichen entfernte."""
    seen = {}

    def fake_popen(args, **kwargs):
        seen["args"] = args
        seen["kwargs"] = kwargs

    monkeypatch.setattr(runner.subprocess, "Popen", fake_popen)
    target = tmp_path / "Claude starten"
    target.mkdir()
    runner._spawn(["cmd", "/K", "claude"], target)

    assert seen["args"] == ["cmd", "/K", "claude"]
    assert seen["kwargs"].get("shell") is not True
    assert seen["kwargs"]["cwd"] == str(target)


# --- Neues Projekt anlegen ------------------------------------------------


def test_create_makes_folder_and_returns_path(tmp_path):
    path = runner.create(tmp_path, "Neues Projekt")
    assert path == tmp_path / "Neues Projekt"
    assert path.is_dir()


def test_create_strips_surrounding_whitespace(tmp_path):
    path = runner.create(tmp_path, "   Neu   ")
    assert path == tmp_path / "Neu"
    assert path.is_dir()


def test_create_rejects_empty_name(tmp_path):
    with pytest.raises(runner.RunnerError):
        runner.create(tmp_path, "   ")


@pytest.mark.parametrize("bad", list(runner.FORBIDDEN_CHARS))
def test_create_rejects_forbidden_characters(tmp_path, bad):
    with pytest.raises(runner.RunnerError):
        runner.create(tmp_path, f"Pro{bad}jekt")


def test_create_rejects_reserved_device_name(tmp_path):
    with pytest.raises(runner.RunnerError):
        runner.create(tmp_path, "CON")


def test_create_rejects_existing_folder(tmp_path):
    (tmp_path / "Alpha").mkdir()
    with pytest.raises(runner.RunnerError):
        runner.create(tmp_path, "Alpha")


def test_create_leaves_folder_empty(tmp_path):
    path = runner.create(tmp_path, "Leer")
    assert list(path.iterdir()) == []


def test_create_missing_root_raises(tmp_path):
    with pytest.raises(runner.RunnerError):
        runner.create(tmp_path / "gibtsnicht", "Alpha")


def test_rename_keeps_the_creation_date(tmp_path):
    """Der Ordner wird umbenannt, nicht neu erstellt."""
    p = project_at(tmp_path, "Alpha")
    before = p.created
    runner.rename(p, "Beta", Config())
    after = [x for x in scan(tmp_path) if x.name == "Beta"][0]
    assert after.created == before


# --- Konsolen-Design ------------------------------------------------------


def spawned_command(tmp_path, monkeypatch, call, name="Alpha") -> list[str]:
    """Faengt den Startbefehl ab, den `runner` an Windows uebergeben wuerde."""
    calls = []
    monkeypatch.setattr(runner, "_spawn", lambda args, cwd: calls.append(args))
    call(project_at(tmp_path, name))
    assert len(calls) == 1
    return calls[0]


def test_start_paints_the_console_in_the_theme_colours(tmp_path, monkeypatch):
    """Ohne Angabe startet das CRT-Design - mit den Farben aus `theme`."""
    command = spawned_command(tmp_path, monkeypatch, runner.start)
    assert f"]11;{theme.BG}\\" in command[-1]
    assert f"]10;{theme.GREEN}\\" in command[-1]


def test_start_clears_the_screen_before_claude_runs(tmp_path, monkeypatch):
    """`cls` malt neu - und wischt die Sequenz weg, falls eine alte
    Konsole sie nicht versteht und stattdessen als Text ausgibt."""
    command = spawned_command(tmp_path, monkeypatch, runner.start)
    assert command[-1].endswith("&cls&claude")


def test_start_in_classic_style_leaves_the_console_alone(tmp_path, monkeypatch):
    command = spawned_command(
        tmp_path, monkeypatch, lambda p: runner.start(p, style="classic")
    )
    assert command == ["cmd", "/K", "claude"]


def test_open_terminal_paints_the_console_too(tmp_path, monkeypatch):
    """Auch ohne Agent darin faerbt sich die Konsole - genau wie beim Start.

    Geprueft wird gegen `_osc` selbst: der Vorspann traegt echte
    ESC-Steuerzeichen, und die schreibt man nicht von Hand in einen Test.
    """
    command = spawned_command(tmp_path, monkeypatch, runner.open_terminal)
    assert command[:2] == ["cmd", "/K"]
    assert runner._osc(11, theme.BG) in command[-1]
    assert runner._osc(10, theme.GREEN) in command[-1]


def test_an_unknown_style_falls_back_to_the_plain_console(tmp_path, monkeypatch):
    """Eine von Hand verstellte config.json darf den Start nicht kippen."""
    command = spawned_command(
        tmp_path, monkeypatch, lambda p: runner.start(p, style="neon")
    )
    assert command == ["cmd", "/K", "claude"]


# --- Geerbte Sitzungsmarker ------------------------------------------------


def spawned_env(tmp_path, monkeypatch) -> dict[str, str]:
    """Die Umgebung, die `_spawn` an die neue Konsole uebergeben wuerde."""
    seen = {}
    monkeypatch.setattr(
        runner.subprocess, "Popen", lambda args, **kwargs: seen.update(kwargs)
    )
    runner._spawn(["cmd", "/K", "claude"], tmp_path)
    return seen["env"]


def test_spawn_strips_an_inherited_child_session_marker(tmp_path, monkeypatch):
    """Sonst haelt sich das Claude in der Konsole fuer eine Unter-Sitzung
    und schreibt kein Transcript mehr."""
    monkeypatch.setenv("CLAUDE_CODE_CHILD_SESSION", "1")
    assert "CLAUDE_CODE_CHILD_SESSION" not in spawned_env(tmp_path, monkeypatch)


def test_spawn_strips_every_known_session_marker(tmp_path, monkeypatch):
    for name in runner.SESSION_MARKERS:
        monkeypatch.setenv(name, "geerbt")
    env = spawned_env(tmp_path, monkeypatch)
    assert [n for n in runner.SESSION_MARKERS if n in env] == []


def test_spawn_keeps_the_rest_of_the_environment(tmp_path, monkeypatch):
    monkeypatch.setenv("CLAUDE_CODE_CHILD_SESSION", "1")
    monkeypatch.setenv("EIGENE_VARIABLE", "bleibt")
    env = spawned_env(tmp_path, monkeypatch)
    assert env["EIGENE_VARIABLE"] == "bleibt"
    assert "PATH" in env


def test_spawn_keeps_claude_settings_that_are_not_markers(tmp_path, monkeypatch):
    """Namentliche Liste, kein Kahlschlag: was der Nutzer selbst dauerhaft
    gesetzt hat, muss die Konsole erreichen."""
    monkeypatch.setenv("ANTHROPIC_API_KEY", "geheim")
    monkeypatch.setenv("CLAUDE_CODE_FORCE_SESSION_PERSISTENCE", "1")
    env = spawned_env(tmp_path, monkeypatch)
    assert env["ANTHROPIC_API_KEY"] == "geheim"
    assert env["CLAUDE_CODE_FORCE_SESSION_PERSISTENCE"] == "1"


# --- Start als Administrator ----------------------------------------------
#
# Erhoehen kann `subprocess.Popen` nicht: dafuer gibt es unter Windows nur
# `ShellExecuteW` mit dem Verb 'runas'. Der Befehl bleibt derselbe, nur der
# Weg dorthin ist ein anderer.


@pytest.fixture
def elevated(monkeypatch):
    """Faengt ab, was an `ShellExecuteW` ginge. Liefert die Aufrufe."""
    calls = []

    def fake(program, params, cwd):
        calls.append((program, params, cwd))
        return 42  # alles ueber 32 heisst: gestartet

    monkeypatch.setattr(runner, "_shell_execute", fake)
    return calls


@pytest.fixture
def no_markers(monkeypatch):
    """Keine geerbte Claude-Sitzung - der Normalfall aus dem Explorer."""
    for name in runner.SESSION_MARKERS:
        monkeypatch.delenv(name, raising=False)


def test_start_as_admin_runs_the_same_command_elevated(
    tmp_path, monkeypatch, agents_in_path, elevated, no_markers
):
    """Es laeuft derselbe Agent, nur mit anderen Rechten - vor ihm steht
    lediglich der Wechsel in den Projektordner, den der erhoehte Prozess
    nicht mitbekommt."""
    unelevated = []
    monkeypatch.setattr(runner, "_spawn", lambda args, cwd: unelevated.append(args))
    p = project_at(tmp_path, "Alpha")

    runner.start(p, "claude", "classic", admin=True)

    assert unelevated == []
    assert elevated == [("cmd", f'/K "cd /d "{p.path}"&claude"', str(p.path))]


def test_start_without_admin_stays_unelevated(
    tmp_path, monkeypatch, agents_in_path, elevated
):
    calls = []
    monkeypatch.setattr(runner, "_spawn", lambda args, cwd: calls.append(args))
    p = project_at(tmp_path, "Alpha")

    runner.start(p, "claude", "classic")

    assert calls == [["cmd", "/K", "claude"]]
    assert elevated == []


def test_the_elevated_start_keeps_the_crt_prologue(
    tmp_path, agents_in_path, elevated, no_markers
):
    p = project_at(tmp_path, "Alpha")
    runner.start(p, "claude", "crt", admin=True)
    (_program, params, _cwd), = elevated
    assert runner._osc(11, theme.BG) in params
    assert params.endswith("&cls&claude\"")


def test_the_elevated_start_quotes_the_command_for_windows(
    tmp_path, agents_in_path, elevated, no_markers
):
    """`ShellExecuteW` nimmt eine Zeile, keine Liste - die &-Kette muss
    also in Anfuehrungszeichen, sonst zerlegt sie jemand anders."""
    p = project_at(tmp_path, "Mit Leerzeichen")
    runner.start(p, "claude", "crt", admin=True)
    (_program, params, cwd), = elevated
    assert params.startswith("/K \"")
    assert cwd == str(p.path)


def test_open_terminal_as_admin_runs_elevated(
    tmp_path, monkeypatch, elevated, no_markers
):
    unelevated = []
    monkeypatch.setattr(runner, "_spawn", lambda args, cwd: unelevated.append(args))
    p = project_at(tmp_path, "Alpha")

    runner.open_terminal(p, "classic", admin=True)

    assert unelevated == []
    assert elevated == [("cmd", f'/K "cd /d "{p.path}""', str(p.path))]


def test_a_refused_uac_prompt_says_so(tmp_path, monkeypatch, agents_in_path):
    """Klickt man im Windows-Dialog auf 'Nein', darf der Knopf nicht
    kommentarlos nichts tun."""
    monkeypatch.setattr(runner, "_shell_execute", lambda *a: runner.SE_ERR_ACCESSDENIED)
    p = project_at(tmp_path, "Alpha")

    with pytest.raises(runner.RunnerError) as error:
        runner.start(p, "claude", "classic", admin=True)
    assert "abgelehnt" in str(error.value).lower()


def test_a_failed_elevated_start_is_reported(tmp_path, monkeypatch, agents_in_path):
    monkeypatch.setattr(runner, "_shell_execute", lambda *a: 2)
    p = project_at(tmp_path, "Alpha")

    with pytest.raises(runner.RunnerError):
        runner.start(p, "claude", "classic", admin=True)


# --- Sitzungsmarker in der erhoehten Konsole -------------------------------
#
# Ein erhoehter Prozess bekommt seine Umgebung nicht von uns: `_child_env`
# greift dort nicht. Die Marker werden deshalb in der Konsole selbst
# geloescht - `set NAME=` ohne Wert entfernt eine Variable.


def test_the_elevated_console_clears_an_inherited_session_marker(
    tmp_path, monkeypatch, agents_in_path, elevated, no_markers
):
    monkeypatch.setenv("CLAUDE_CODE_CHILD_SESSION", "1")
    p = project_at(tmp_path, "Alpha")

    runner.start(p, "claude", "classic", admin=True)

    (_program, params, _cwd), = elevated
    assert "set CLAUDE_CODE_CHILD_SESSION=" in params
    assert params.endswith("claude\"")


def test_the_elevated_console_clears_every_known_marker(
    tmp_path, monkeypatch, agents_in_path, elevated
):
    for name in runner.SESSION_MARKERS:
        monkeypatch.setenv(name, "geerbt")
    p = project_at(tmp_path, "Alpha")

    runner.start(p, "claude", "classic", admin=True)

    (_program, params, _cwd), = elevated
    assert all(f"set {name}=" in params for name in runner.SESSION_MARKERS)


def test_without_inherited_markers_nothing_is_prepended(
    tmp_path, agents_in_path, elevated, no_markers
):
    """Der Normalfall - aus dem Explorer gestartet - bleibt schlicht:
    Ordnerwechsel und Agent, kein `set` dazwischen."""
    p = project_at(tmp_path, "Alpha")
    runner.start(p, "claude", "classic", admin=True)
    assert elevated == [("cmd", f'/K "cd /d "{p.path}"&claude"', str(p.path))]


def test_the_plain_elevated_terminal_gets_a_console_for_the_cleanup(
    tmp_path, monkeypatch, elevated
):
    """Ohne Vorspann gibt es keine &-Kette, an die sich `set` haengen
    koennte - dann bekommt `cmd` eine."""
    monkeypatch.setenv("CLAUDECODE", "1")
    p = project_at(tmp_path, "Alpha")

    runner.open_terminal(p, "classic", admin=True)

    (_program, params, _cwd), = elevated
    assert params.startswith("/K ")
    assert "set CLAUDECODE=" in params


# --- Der Ordner in der erhoehten Konsole -----------------------------------
#
# `ShellExecuteW` bekommt den Ordner uebergeben, benutzt ihn beim Verb
# 'runas' aber nicht: den erhoehten Prozess startet nicht der Launcher,
# sondern der Dienst hinter der Rechteerhoehung - und der setzt sein
# eigenes Verzeichnis. Gemessen landet die Konsole in C:\Windows\System32.
# Der Wechsel muss deshalb im Befehl selbst stehen.


def test_the_elevated_start_changes_into_the_project_folder(
    tmp_path, agents_in_path, elevated, no_markers
):
    p = project_at(tmp_path, "Mit Leerzeichen")

    runner.start(p, "claude", "classic", admin=True)

    (_program, params, _cwd), = elevated
    assert params.startswith(f'/K "cd /d "{p.path}"&')
    assert params.endswith('claude"')


def test_the_elevated_terminal_changes_into_the_project_folder(
    tmp_path, elevated, no_markers
):
    p = project_at(tmp_path, "Mit Leerzeichen")

    runner.open_terminal(p, "classic", admin=True)

    (_program, params, _cwd), = elevated
    assert params == f'/K "cd /d "{p.path}""'


def test_the_elevated_folder_change_comes_before_the_cleanup(
    tmp_path, monkeypatch, agents_in_path, elevated, no_markers
):
    """Erst der Ordner, dann die Marker - sonst stuende das Aufraeumen in
    einer Konsole, die noch woanders steht. Reihenfolge statt Zufall."""
    monkeypatch.setenv("CLAUDECODE", "1")
    p = project_at(tmp_path, "Alpha")

    runner.start(p, "claude", "classic", admin=True)

    (_program, params, _cwd), = elevated
    assert params.index("cd /d") < params.index("set CLAUDECODE=")


# --- Die Notiz eines Projekts ---------------------------------------------


@pytest.fixture
def notepad(monkeypatch):
    """Faengt ab, was `open_note` starten wuerde."""
    calls = []
    monkeypatch.setattr(
        runner, "_spawn", lambda args, cwd, console=True: calls.append((args, cwd))
    )
    return calls


def test_the_note_lives_in_the_project_folder(tmp_path):
    p = project_at(tmp_path, "Alpha")
    assert runner.note_path(p) == tmp_path / "Alpha" / NOTE_NAME


def test_opening_a_missing_note_creates_it(tmp_path, notepad):
    p = project_at(tmp_path, "Alpha")
    runner.open_note(p)
    assert runner.note_path(p).is_file()


def test_a_created_note_carries_the_project_name(tmp_path, notepad):
    """Notepad soll nicht mit einem leeren Blatt aufgehen - die Kopfzeile
    sagt, wovon die Rede ist."""
    p = project_at(tmp_path, "Alpha")
    runner.open_note(p)
    assert "Alpha" in runner.note_path(p).read_text(encoding="utf-8")


def test_an_existing_note_is_never_overwritten(tmp_path, notepad):
    p = project_at(tmp_path, "Alpha")
    runner.note_path(p).write_text("Nicht anfassen.", encoding="utf-8")
    runner.open_note(p)
    assert runner.note_path(p).read_text(encoding="utf-8") == "Nicht anfassen."


def test_opening_the_note_starts_notepad_on_it(tmp_path, notepad):
    p = project_at(tmp_path, "Alpha")
    runner.open_note(p)
    (args, cwd), = notepad
    assert args[0] == "notepad"
    assert Path(args[1]) == runner.note_path(p)
    assert cwd == p.path


def test_opening_the_note_opens_no_console(tmp_path, monkeypatch):
    """Sonst blitzte bei jedem Klick ein schwarzes Fenster auf."""
    seen = {}
    monkeypatch.setattr(
        runner,
        "_spawn",
        lambda args, cwd, console=True: seen.update(console=console),
    )
    runner.open_note(project_at(tmp_path, "Alpha"))
    assert seen["console"] is False


def test_opening_the_note_of_a_vanished_folder_raises(tmp_path, notepad):
    p = project_at(tmp_path, "Alpha")
    p.path.rmdir()
    with pytest.raises(runner.RunnerError):
        runner.open_note(p)


def test_a_note_that_cannot_be_written_is_reported(tmp_path, notepad, monkeypatch):
    """Ohne Meldung taete der Klick auf das Symbol kommentarlos nichts -
    die .exe hat keine Konsole fuer einen Traceback."""
    p = project_at(tmp_path, "Alpha")

    def kaputt(*args, **kwargs):
        raise OSError(13, "Zugriff verweigert")

    monkeypatch.setattr(Path, "write_text", kaputt)
    with pytest.raises(runner.RunnerError):
        runner.open_note(p)
    assert notepad == []


# --- Umbenennen und Loeschen nehmen den Agenten mit -----------------------


def test_rename_moves_the_remembered_agent(tmp_path):
    p = project_at(tmp_path, "Alpha")
    cfg = Config()
    cfg.remember_agent("Alpha", "codex")
    runner.rename(p, "Beta", cfg)
    assert cfg.agent_of("Beta") == "codex"
    assert cfg.agent_of("Alpha") == ""


def test_delete_forgets_the_remembered_agent(tmp_path, monkeypatch):
    """Sonst bliebe der Eintrag in der config.json stehen - und ein
    spaeter gleichnamiges Projekt erbte ihn."""
    monkeypatch.setattr(runner, "send_to_trash", lambda path: None)
    p = project_at(tmp_path, "Alpha")
    cfg = Config()
    cfg.remember_agent("Alpha", "codex")

    runner.delete(p, cfg)

    assert cfg.agent_of("Alpha") == ""


# --- Die Notiz entsteht gefuellt ------------------------------------------


@pytest.fixture
def kein_stand(monkeypatch):
    """Ersetzt die Standerhebung durch etwas Wiedererkennbares.

    Die echte liest Sitzungsarchive des pruefenden Rechners - davon darf
    kein Test abhaengen.
    """
    monkeypatch.setattr(
        runner.activity, "status_block", lambda pfad: "## Stand vom HEUTE\n\n- etwas\n"
    )


def test_a_created_note_already_carries_the_status(tmp_path, notepad, kein_stand):
    """Genau der Punkt: ein leeres Blatt war die Beschwerde."""
    p = project_at(tmp_path, "Alpha")
    runner.open_note(p)
    text = runner.note_path(p).read_text(encoding="utf-8")
    assert "# Aufgaben — Alpha" in text
    assert "## Stand vom HEUTE" in text


def test_opening_an_existing_note_adds_nothing(tmp_path, notepad, kein_stand):
    """Nur beim Anlegen. Sonst waeche die Datei bei jedem Blick hinein."""
    p = project_at(tmp_path, "Alpha")
    runner.note_path(p).write_text("Mein Text.\n", encoding="utf-8")
    runner.open_note(p)
    assert runner.note_path(p).read_text(encoding="utf-8") == "Mein Text.\n"


def test_a_status_that_cannot_be_gathered_still_gives_a_note(tmp_path, notepad, monkeypatch):
    """Die Sitzungsarchive sind ein undokumentiertes Format. Bricht das
    Auslesen, soll trotzdem eine Notiz aufgehen - ohne Stand eben."""

    def kaputt(pfad):
        raise RuntimeError("Format geaendert")

    monkeypatch.setattr(runner.activity, "status_block", kaputt)
    p = project_at(tmp_path, "Alpha")
    runner.open_note(p)
    assert "# Aufgaben — Alpha" in runner.note_path(p).read_text(encoding="utf-8")


# --- Stand einfuegen ------------------------------------------------------


def test_inserting_a_status_creates_the_note_if_needed(tmp_path, notepad, kein_stand):
    p = project_at(tmp_path, "Alpha")
    runner.insert_status(p)
    text = runner.note_path(p).read_text(encoding="utf-8")
    assert "# Aufgaben — Alpha" in text
    assert "## Stand vom HEUTE" in text


def test_the_new_block_lands_under_the_heading(tmp_path, notepad, kein_stand):
    """Oben, damit in Notepad das Neueste ohne Scrollen dasteht."""
    p = project_at(tmp_path, "Alpha")
    runner.note_path(p).write_text(
        "# Aufgaben — Alpha\n\n## Stand vom GESTERN\n\n- alt\n", encoding="utf-8"
    )
    runner.insert_status(p)
    zeilen = runner.note_path(p).read_text(encoding="utf-8").splitlines()
    assert zeilen[0] == "# Aufgaben — Alpha"
    assert zeilen.index("## Stand vom HEUTE") < zeilen.index("## Stand vom GESTERN")


def test_nothing_the_user_wrote_is_lost(tmp_path, notepad, kein_stand):
    p = project_at(tmp_path, "Alpha")
    runner.note_path(p).write_text(
        "# Aufgaben — Alpha\n\n- meine eigene Zeile\n", encoding="utf-8"
    )
    runner.insert_status(p)
    assert "- meine eigene Zeile" in runner.note_path(p).read_text(encoding="utf-8")


def test_a_note_without_a_heading_keeps_its_content(tmp_path, notepad, kein_stand):
    """Von Hand angelegt, ohne Ueberschrift - der Text darf nicht unter
    die neue Ueberschrift rutschen und dadurch verschwinden."""
    p = project_at(tmp_path, "Alpha")
    runner.note_path(p).write_text("nur eine lose Zeile\n", encoding="utf-8")
    runner.insert_status(p)
    text = runner.note_path(p).read_text(encoding="utf-8")
    assert text.startswith("# Aufgaben — Alpha")
    assert "nur eine lose Zeile" in text


def test_inserting_twice_keeps_both_blocks(tmp_path, notepad, monkeypatch):
    p = project_at(tmp_path, "Alpha")
    monkeypatch.setattr(runner.activity, "status_block", lambda pfad: "## Stand A\n")
    runner.insert_status(p)
    monkeypatch.setattr(runner.activity, "status_block", lambda pfad: "## Stand B\n")
    runner.insert_status(p)
    text = runner.note_path(p).read_text(encoding="utf-8")
    assert text.index("## Stand B") < text.index("## Stand A")


def test_inserting_a_status_opens_the_note(tmp_path, notepad, kein_stand):
    p = project_at(tmp_path, "Alpha")
    runner.insert_status(p)
    (args, _cwd), = notepad
    assert args[0] == "notepad"
    assert Path(args[1]) == runner.note_path(p)


def test_inserting_into_a_vanished_folder_raises(tmp_path, notepad, kein_stand):
    p = project_at(tmp_path, "Alpha")
    p.path.rmdir()
    with pytest.raises(runner.RunnerError):
        runner.insert_status(p)


def test_the_heading_survives_an_umlaut_name(tmp_path, notepad, kein_stand):
    p = project_at(tmp_path, "Aufräum App")
    runner.insert_status(p)
    assert "# Aufgaben — Aufräum App" in runner.note_path(p).read_text(encoding="utf-8")


def test_writing_the_note_leaves_the_folder_time_alone(tmp_path, notepad, kein_stand):
    """HQ soll die Liste nicht mit dem eigenen Schreiben umsortieren.

    Eine neue Datei ist ein neuer Eintrag im Verzeichnis, und davon hebt
    Windows die Ordnerzeit an. In einem leeren Projekt ist die Notiz die
    einzige Datei - dann faellt `newest_change` auf genau diese Ordnerzeit
    zurueck, und das Projekt schoebe sich nach oben, ohne dass jemand
    darin gearbeitet haette.
    """
    p = project_at(tmp_path, "Alpha")
    alt = time.time() - 60 * 86400
    os.utime(p.path, (alt, alt))

    runner.open_note(p)

    assert p.path.stat().st_mtime == pytest.approx(alt, abs=2)
    assert runner.note_path(p).is_file(), "die Notiz soll trotzdem da sein"


def test_inserting_a_status_leaves_the_folder_time_alone(tmp_path, notepad, kein_stand):
    p = project_at(tmp_path, "Alpha")
    alt = time.time() - 60 * 86400
    os.utime(p.path, (alt, alt))

    runner.insert_status(p)

    assert p.path.stat().st_mtime == pytest.approx(alt, abs=2)


# --- Automatischer Shutdown ------------------------------------------------


def test_schedule_shutdown_calls_windows_shutdown(tmp_path, monkeypatch):
    calls = []
    monkeypatch.setattr(
        runner, "_spawn", lambda args, cwd, console=True: calls.append((args, console))
    )
    runner.schedule_shutdown(30)
    (args, console), = calls
    assert args == ["shutdown", "/s", "/t", "1800"]
    assert console is False


def test_schedule_shutdown_rounds_fractional_minutes(tmp_path, monkeypatch):
    calls = []
    monkeypatch.setattr(
        runner, "_spawn", lambda args, cwd, console=True: calls.append(args)
    )
    runner.schedule_shutdown(0.5)
    assert calls == [["shutdown", "/s", "/t", "30"]]


def test_cancel_shutdown_calls_windows_shutdown_abort(tmp_path, monkeypatch):
    calls = []
    monkeypatch.setattr(
        runner, "_spawn", lambda args, cwd, console=True: calls.append(args)
    )
    runner.cancel_shutdown()
    assert calls == [["shutdown", "/a"]]


def test_a_folder_time_that_cannot_be_restored_is_no_error(tmp_path, notepad, kein_stand, monkeypatch):
    """Die Notiz ist wichtiger als die Kosmetik am Zeitstempel."""

    def kaputt(*args, **kwargs):
        raise OSError(13, "Zugriff verweigert")

    p = project_at(tmp_path, "Alpha")
    monkeypatch.setattr(runner.os, "utime", kaputt)
    runner.open_note(p)
    assert runner.note_path(p).is_file()


# --- cmd oder PowerShell, mit oder ohne Rueckfragen -----------------------


def test_skip_permissions_adds_the_flag_to_claude_in_cmd(
    tmp_path, monkeypatch, agents_in_path
):
    """Der Schalter haengt nicht mehr an PowerShell."""
    command = spawned_command(
        tmp_path,
        monkeypatch,
        lambda p: runner.start(p, "claude", "classic", skip_permissions=True),
    )
    assert command == ["cmd", "/K", "claude --dangerously-skip-permissions"]


def test_skip_permissions_starts_claude_in_powershell_when_chosen(
    tmp_path, monkeypatch, agents_in_path
):
    command = spawned_command(
        tmp_path,
        monkeypatch,
        lambda p: runner.start(
            p, "claude", "classic", skip_permissions=True, shell="powershell"
        ),
    )
    assert command == [
        "powershell",
        "-NoExit",
        "-Command",
        "claude --dangerously-skip-permissions",
    ]


def test_powershell_without_skip_starts_the_plain_agent(
    tmp_path, monkeypatch, agents_in_path
):
    command = spawned_command(
        tmp_path,
        monkeypatch,
        lambda p: runner.start(p, "codex", "classic", shell="powershell"),
    )
    assert command == ["powershell", "-NoExit", "-Command", "codex"]


def test_skip_permissions_paints_the_powershell_in_crt(
    tmp_path, monkeypatch, agents_in_path
):
    """Der cmd-Vorspann taugt nicht: PowerShell verweigert das `&`."""
    command = spawned_command(
        tmp_path,
        monkeypatch,
        lambda p: runner.start(
            p, "claude", "crt", skip_permissions=True, shell="powershell"
        ),
    )
    script = command[-1]
    assert f"']11;{theme.BG}'" in script
    assert f"']10;{theme.GREEN}'" in script
    assert "&" not in script
    assert '"' not in script
    assert script.endswith("; Clear-Host; claude --dangerously-skip-permissions")


@pytest.mark.parametrize("shell", ["cmd", "powershell"])
def test_skip_permissions_frees_codex_from_its_sandbox(
    tmp_path, monkeypatch, agents_in_path, shell
):
    command = spawned_command(
        tmp_path,
        monkeypatch,
        lambda p: runner.start(
            p, "codex", "crt", skip_permissions=True, shell=shell
        ),
    )
    assert command[-1].endswith(
        "codex --sandbox danger-full-access --ask-for-approval never"
    )


def test_an_unknown_shell_falls_back_to_cmd():
    assert runner.agent_command("claude", "classic", "bash") == [
        "cmd",
        "/K",
        "claude",
    ]


def test_skip_permissions_as_admin_in_cmd_keeps_the_flag(
    tmp_path, agents_in_path, elevated, no_markers
):
    p = project_at(tmp_path, "Alpha")
    runner.start(p, "codex", "classic", admin=True, skip_permissions=True)
    assert elevated == [
        (
            "cmd",
            f'/K "cd /d "{p.path}"&codex --sandbox danger-full-access '
            '--ask-for-approval never"',
            str(p.path),
        )
    ]


def test_skip_permissions_as_admin_changes_into_the_project_in_powershell(
    tmp_path, agents_in_path, elevated, no_markers
):
    p = project_at(tmp_path, "O'Brien")
    runner.start(
        p, "claude", "classic", admin=True, skip_permissions=True, shell="powershell"
    )
    folder = str(p.path).replace("'", "''")
    assert elevated == [
        (
            "powershell",
            f"-NoExit -Command \"Set-Location -LiteralPath '{folder}'; "
            "claude --dangerously-skip-permissions\"",
            str(p.path),
        )
    ]


def test_skip_permissions_as_admin_drops_session_markers(
    tmp_path, monkeypatch, agents_in_path, elevated, no_markers
):
    monkeypatch.setenv("CLAUDECODE", "1")
    runner.start(
        project_at(tmp_path, "Alpha"),
        "claude",
        "crt",
        admin=True,
        skip_permissions=True,
        shell="powershell",
    )
    (_program, params, _cwd), = elevated
    assert "Remove-Item Env:CLAUDECODE -ErrorAction SilentlyContinue" in params
    assert params.count('"') == 2
