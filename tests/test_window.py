"""Durchstichtests gegen das echte Hauptfenster (offscreen).

Sie decken ab, was die Modultests nicht sehen: dass das Fenster die
richtige Aktion aufruft, die Auswahl korrekt aufloest und nach jeder
Aktion neu scannt. Die Dialoge und die Betriebssystemaufrufe werden
ersetzt, sodass nichts wirklich startet oder geloescht wird.
"""

from __future__ import annotations

import json
import os
import time
from pathlib import Path

import pytest
from PySide6.QtCore import QEvent, Qt
from PySide6.QtGui import QShortcut
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication

from projecthq import runner
from projecthq.config import AGENT_MARKS, Config
from projecthq.scanner import NOTE_NAME
from projecthq.ui import dialogs, window as window_module
from projecthq.ui.window import MainWindow


@pytest.fixture(scope="session")
def app():
    return QApplication.instance() or QApplication([])


@pytest.fixture
def demo_root(tmp_path: Path) -> Path:
    root = tmp_path / "projekte"
    (root / "Gangland").mkdir(parents=True)
    (root / "Gangland" / "package.json").write_text(
        json.dumps({"scripts": {"dev": "next dev"}}), encoding="utf-8"
    )
    (root / "Tarkov").mkdir()
    (root / "Tarkov" / "main.py").write_text("print(1)", encoding="utf-8")
    (root / "Leer").mkdir()
    return root


@pytest.fixture
def win(app, demo_root, tmp_path) -> MainWindow:
    config = Config()
    config.projects_root = demo_root
    return MainWindow(config, tmp_path / "config.json")


@pytest.fixture(autouse=True)
def nothing_blocks(monkeypatch):
    """Kein Test darf ein echtes modales Fenster oeffnen.

    `_start` fragt seit dem Startdialog, womit gestartet werden soll.
    Ohne Ersatz bliebe `exec()` stehen und der ganze Lauf haengt - genau
    das ist beim ersten Versuch passiert. Ersetzt wird der Dialog durch
    die zuletzt getroffene Wahl, was dem Enter-Druck entspricht.

    Ausserdem liegen beide Agenten scheinbar im PATH, damit die
    Starttests nicht davon abhaengen, was auf dem pruefenden Rechner
    gerade installiert ist. Ein Test, der es anders braucht, setzt
    danach seinen eigenen Ersatz.
    """
    monkeypatch.setattr(
        dialogs,
        "ask_agent",
        lambda parent, project, last, shell=None: dialogs.StartChoice(last, False),
    )
    monkeypatch.setattr(
        runner.shutil,
        "which",
        lambda name: rf"C:\{name}.cmd" if name in ("claude", "codex") else None,
    )


def visible_names(win: MainWindow) -> list[str]:
    return [win.list.item(i).data(Qt.UserRole) for i in range(win.list.count())]


def altern(ordner: Path, sekunden: float) -> None:
    """Setzt Ordner UND Inhalt zurueck.

    Nur den Ordner zurueckzusetzen genuegt nicht mehr: das Datum in der
    Liste ist die juengste Aenderung im ganzen Baum, und die Dateien
    darin waeren weiterhin von eben. Genau darum ging es bei der
    Umstellung - die Ordnerzeit merkt nichts davon, dass in einer Datei
    getippt wurde.
    """
    alt = time.time() - sekunden
    for pfad in sorted(ordner.rglob("*"), reverse=True):
        os.utime(pfad, (alt, alt))
    os.utime(ordner, (alt, alt))


def select(win: MainWindow, name: str) -> None:
    names = visible_names(win)
    assert name in names, f"'{name}' steht nicht in der Liste: {names}"
    win.list.setCurrentRow(names.index(name))


def test_window_lists_all_projects(win):
    assert set(visible_names(win)) == {"Gangland", "Tarkov", "Leer"}


def test_search_filters_live(win):
    win.search.setText("gang")
    assert visible_names(win) == ["Gangland"]
    win.search.setText("")
    assert len(visible_names(win)) == 3


def test_search_is_case_insensitive(win):
    win.search.setText("TARKOV")
    assert visible_names(win) == ["Tarkov"]


def test_start_opens_claude_in_the_project_folder(win, monkeypatch, demo_root):
    calls = []
    monkeypatch.setattr(runner, "_spawn", lambda args, cwd: calls.append((args, cwd)))
    select(win, "Gangland")
    win._start()
    (command, cwd), = calls
    assert cwd == demo_root / "Gangland"
    assert command[-1].endswith("claude")


def test_start_also_works_for_a_project_without_any_files(win, monkeypatch, demo_root):
    calls = []
    monkeypatch.setattr(runner, "_spawn", lambda args, cwd: calls.append((args, cwd)))
    select(win, "Leer")
    win._start()
    (command, cwd), = calls
    assert cwd == demo_root / "Leer"
    assert command[-1].endswith("claude")


def test_rename_updates_list_and_selection(win, monkeypatch, demo_root):
    monkeypatch.setattr(dialogs, "ask_rename", lambda parent, project: "Gangland2")
    select(win, "Gangland")
    win._rename()
    assert "Gangland2" in visible_names(win)
    assert "Gangland" not in visible_names(win)
    assert (demo_root / "Gangland2").is_dir()
    assert win._selected().name == "Gangland2"


def test_rename_error_is_shown_and_list_unchanged(win, monkeypatch):
    monkeypatch.setattr(dialogs, "ask_rename", lambda parent, project: "Tarkov")
    shown = []
    monkeypatch.setattr(dialogs, "show_error", lambda parent, message: shown.append(message))
    select(win, "Gangland")
    win._rename()
    assert shown and "existiert bereits" in shown[0]
    assert "Gangland" in visible_names(win)


def test_delete_removes_project_from_list(win, monkeypatch):
    monkeypatch.setattr(dialogs, "confirm_delete", lambda parent, project: True)
    monkeypatch.setattr(runner, "send_to_trash", lambda path: Path(path).rmdir())
    select(win, "Leer")
    win._delete()
    assert "Leer" not in visible_names(win)


def test_delete_can_be_cancelled(win, monkeypatch):
    monkeypatch.setattr(dialogs, "confirm_delete", lambda parent, project: False)
    monkeypatch.setattr(runner, "send_to_trash", lambda path: pytest.fail("darf nicht loeschen"))
    select(win, "Leer")
    win._delete()
    assert "Leer" in visible_names(win)


def test_missing_root_shows_warning_and_empty_list(app, tmp_path):
    config = Config()
    config.projects_root = tmp_path / "gibtsnicht"
    win = MainWindow(config, tmp_path / "config.json")
    assert visible_names(win) == []
    assert "NICHT GEFUNDEN" in win._header_text


def test_escape_clears_search_first(win):
    win.search.setText("gang")
    win._on_escape()
    assert win.search.text() == ""
    assert set(visible_names(win)) == {"Gangland", "Tarkov", "Leer"}


def test_long_path_is_elided_in_status(win, demo_root):
    name = "Lang" * 20
    (demo_root / name).mkdir()
    win.refresh()
    select(win, name)
    assert win._status_text.endswith(name)
    assert len(win.status.text()) < len(win._status_text)
    assert "…" in win.status.text()


def test_action_error_is_reported_not_raised(win, monkeypatch):
    def boom(project):
        raise runner.RunnerError("kaputt")

    shown = []
    monkeypatch.setattr(dialogs, "show_error", lambda parent, message: shown.append(message))
    select(win, "Gangland")
    win._run(boom)
    assert shown == ["kaputt"]


def test_overlay_is_transparent_for_mouse(win):
    assert win.overlay.testAttribute(Qt.WA_TransparentForMouseEvents) is True


def test_window_module_exposes_title():
    assert window_module.TITLE.replace(" ", "") == "CODE/XHQ"


# --- Neues Projekt anlegen ------------------------------------------------


def test_new_project_creates_folder_selects_it_and_starts_claude(
    win, monkeypatch, demo_root
):
    monkeypatch.setattr(dialogs, "ask_new_name", lambda parent: "Frisch")
    started = []
    monkeypatch.setattr(
        runner,
        "start",
        lambda project, agent, style, admin, **_: started.append(project.name),
    )

    win._new_project()

    assert (demo_root / "Frisch").is_dir()
    assert "Frisch" in visible_names(win)
    assert win._selected().name == "Frisch"
    assert started == ["Frisch"]


def test_new_project_can_be_cancelled(win, monkeypatch, demo_root):
    monkeypatch.setattr(dialogs, "ask_new_name", lambda parent: None)
    monkeypatch.setattr(
        runner, "start", lambda project: pytest.fail("darf nicht starten")
    )
    before = set(visible_names(win))

    win._new_project()

    assert set(visible_names(win)) == before


def test_new_project_with_existing_name_reports_the_error(win, monkeypatch):
    monkeypatch.setattr(dialogs, "ask_new_name", lambda parent: "Gangland")
    shown = []
    monkeypatch.setattr(dialogs, "show_error", lambda parent, message: shown.append(message))
    monkeypatch.setattr(
        runner, "start", lambda project: pytest.fail("darf nicht starten")
    )

    win._new_project()

    assert shown and "existiert bereits" in shown[0]


# --- Beide Daten in der Liste ---------------------------------------------


def test_list_row_shows_creation_and_modification_date(win, demo_root):
    long_ago = time.time() - 400 * 24 * 3600
    altern(demo_root / "Gangland", 400 * 24 * 3600)
    win._reload()
    select(win, "Gangland")

    row = win.list.currentItem().text()
    project = win._selected()
    assert time.strftime("%d.%m.%Y", time.localtime(project.created)) in row
    assert time.strftime("%d.%m.%Y", time.localtime(long_ago)) in row


def test_status_shows_the_project_path(win, demo_root):
    select(win, "Tarkov")
    assert "Tarkov" in win.status.text()


# --- Sortieren per Klick auf die Ueberschrift ------------------------------


def click_column(win: MainWindow, key: str) -> None:
    QTest.mouseClick(win.column_labels[key], Qt.LeftButton)


def test_the_column_head_is_indented_like_a_list_row(win):
    """Kopf und Zeilen ruecken gleich weit ein.

    Der Einzug einer Zeile ist der Rahmen der Liste, ihr linker Rand und
    ihr Innenabstand. Rechnet der Kopf anders, stehen die Ueberschriften
    neben ihren Spalten statt darueber.
    """
    from projecthq.theme import LIST_BORDER, ROW_MARKER, ROW_PADDING

    left = win.columns.layout().contentsMargins().left()
    assert left == LIST_BORDER + ROW_MARKER + ROW_PADDING


def test_header_names_all_four_columns(win):
    texts = " ".join(label.text().upper() for label in win.column_labels.values())
    for name in ("PROJEKT", "TYP", "ERSTELLT", "BEARBEITET"):
        assert name in texts


def test_clicking_the_project_column_sorts_alphabetically(win):
    click_column(win, "name")
    assert visible_names(win) == ["Gangland", "Leer", "Tarkov"]


def test_clicking_the_same_column_again_reverses_the_order(win):
    click_column(win, "name")
    click_column(win, "name")
    assert visible_names(win) == ["Tarkov", "Leer", "Gangland"]


def test_dates_start_with_the_newest_entry(win, demo_root):
    altern(demo_root / "Tarkov", 400 * 24 * 3600)
    win._reload()

    click_column(win, "name")  # erst weg von der Vorgabe
    click_column(win, "mtime")  # erster Klick auf ein Datum: juengstes oben
    assert visible_names(win)[-1] == "Tarkov"

    click_column(win, "mtime")  # zweiter Klick dreht um
    assert visible_names(win)[0] == "Tarkov"


def test_the_active_column_is_marked_with_an_arrow(win):
    click_column(win, "name")
    assert "▲" in win.column_labels["name"].text()
    assert "▼" not in win.column_labels["name"].text()
    assert all(
        "▲" not in label.text() and "▼" not in label.text()
        for key, label in win.column_labels.items()
        if key != "name"
    )

    click_column(win, "name")
    assert "▼" in win.column_labels["name"].text()


def test_the_column_heads_keep_their_labels_when_sorted(win):
    click_column(win, "created")
    assert win.column_labels["created"].text().upper().startswith("ERSTELLT")


def test_the_chosen_order_is_written_to_the_config_file(win, tmp_path):
    click_column(win, "name")
    data = json.loads((tmp_path / "config.json").read_text(encoding="utf-8"))
    assert data["sort_key"] == "name"
    assert data["sort_desc"] is False


def test_the_window_starts_with_the_stored_order(app, demo_root, tmp_path):
    config = Config()
    config.projects_root = demo_root
    config.sort_key = "name"
    config.sort_desc = True
    win = MainWindow(config, tmp_path / "config.json")
    assert visible_names(win) == ["Tarkov", "Leer", "Gangland"]
    assert "▼" in win.column_labels["name"].text()


def test_the_selected_project_stays_selected_after_sorting(win):
    select(win, "Tarkov")
    click_column(win, "name")
    assert win._selected().name == "Tarkov"


def test_sorting_keeps_the_active_search_filter(win):
    win.search.setText("a")
    before = set(visible_names(win))
    click_column(win, "name")
    assert set(visible_names(win)) == before


# --- Einstellungen --------------------------------------------------------


def test_start_uses_the_console_style_from_the_config(win, monkeypatch):
    calls = []
    monkeypatch.setattr(runner, "_spawn", lambda args, cwd: calls.append(args))
    win.config.console_style = "classic"
    select(win, "Gangland")
    win._start()
    assert calls == [["cmd", "/K", "claude"]]


def test_terminal_uses_the_console_style_from_the_config(win, monkeypatch):
    calls = []
    monkeypatch.setattr(runner, "_spawn", lambda args, cwd: calls.append(args))
    monkeypatch.setattr(runner.shutil, "which", lambda name: None)
    win.config.console_style = "classic"
    select(win, "Gangland")
    win._open_terminal()
    assert calls == [["cmd"]]


def test_settings_write_a_changed_style_to_disk(win, monkeypatch, tmp_path):
    def stub(parent, config):
        config.console_style = "classic"
        return True

    monkeypatch.setattr(dialogs, "open_settings", stub)
    win._open_settings()

    saved = json.loads((tmp_path / "config.json").read_text(encoding="utf-8"))
    assert saved["console_style"] == "classic"


def test_settings_without_a_change_write_nothing(win, monkeypatch, tmp_path):
    monkeypatch.setattr(dialogs, "open_settings", lambda parent, config: False)
    win._open_settings()
    assert not (tmp_path / "config.json").exists()


def test_settings_with_a_changed_theme_recolour_the_running_window(
    win, monkeypatch, tmp_path
):
    """Der Wechsel wirkt sofort - ohne Neustart."""
    from projecthq import theme as theme_module

    def stub(parent, config):
        config.app_theme = "dos"
        return True

    monkeypatch.setattr(dialogs, "open_settings", stub)
    win._open_settings()

    assert theme_module.CURRENT_THEME == "dos"
    assert theme_module.GREEN in win.styleSheet()
    assert QApplication.instance().styleSheet() == win.styleSheet()


def test_settings_without_a_theme_change_leave_the_theme_alone(
    win, monkeypatch, tmp_path
):
    from projecthq import theme as theme_module

    monkeypatch.setattr(dialogs, "open_settings", lambda parent, config: True)
    win._open_settings()

    assert theme_module.CURRENT_THEME == theme_module.DEFAULT_THEME


def test_settings_with_a_new_root_rescan_the_list(win, monkeypatch, tmp_path):
    other = tmp_path / "woanders"
    (other / "Solo").mkdir(parents=True)

    def stub(parent, config):
        config.projects_root = other
        return True

    monkeypatch.setattr(dialogs, "open_settings", stub)
    win._open_settings()
    assert visible_names(win) == ["Solo"]


def test_a_new_language_relabels_the_running_window(win, monkeypatch, tmp_path):
    """Wie das Design: der Wechsel wirkt sofort, ohne Neustart."""

    def stub(parent, config):
        config.language = "en"
        return True

    monkeypatch.setattr(dialogs, "open_settings", stub)
    win._open_settings()

    assert [b.text() for b in win.sidebar_buttons][0] == "▶ START  F5"
    assert win.sidebar_buttons[2].text() == "RENAME  F2"
    assert win.delete_button.text() == "DELETE  DEL"
    assert win.search.placeholderText() == "search ..."
    assert win.column_labels["kind"].text().startswith("TYPE")
    assert "PROJECTS" in win._header_text
    assert [a.text() for a in win._context_menu().actions()][0] == "Start"
    saved = json.loads((tmp_path / "config.json").read_text(encoding="utf-8"))
    assert saved["language"] == "en"


# --- Womit gestartet wird ---------------------------------------------------


@pytest.fixture
def chooses(monkeypatch):
    """Ersetzt den Startdialog. Liefert, was 'gewaehlt' wurde."""

    def choose(agent):
        monkeypatch.setattr(
            dialogs,
            "ask_agent",
            lambda parent, project, last, shell=None: dialogs.StartChoice(agent, False),
        )

    return choose


@pytest.fixture
def started(monkeypatch):
    """Faengt ab, womit `runner.start` aufgerufen wird."""
    calls = []
    monkeypatch.setattr(
        runner,
        "start",
        lambda project, agent, style, admin, skip_permissions=False, shell="cmd": calls.append(
            (project.name, agent, style, admin)
            + (("skip",) if skip_permissions else ())
            + ((shell,) if shell != "cmd" else ())
        ),
    )
    return calls


def test_starting_asks_which_agent_to_use(win, monkeypatch, started):
    asked = []

    def fake_ask(parent, project, last, shell=None):
        asked.append((project.name, last))
        return dialogs.StartChoice("codex", False)

    monkeypatch.setattr(dialogs, "ask_agent", fake_ask)
    select(win, "Tarkov")
    win._start()

    assert asked == [("Tarkov", "claude")]
    assert started == [("Tarkov", "codex", "crt", False)]


def test_cancelling_the_dialog_starts_nothing(win, monkeypatch, started):
    monkeypatch.setattr(dialogs, "ask_agent", lambda parent, project, last, shell=None: None)
    select(win, "Tarkov")
    win._start()
    assert started == []


def test_the_choice_is_remembered_for_the_next_start(win, chooses, started):
    chooses("codex")
    select(win, "Tarkov")
    win._start()
    assert win.config.last_agent == "codex"


def test_the_remembered_choice_is_written_to_the_config_file(
    win, chooses, started, tmp_path
):
    chooses("codex")
    select(win, "Tarkov")
    win._start()

    saved = json.loads((tmp_path / "config.json").read_text(encoding="utf-8"))
    assert saved["last_agent"] == "codex"


def test_the_dialog_offers_the_remembered_choice_next_time(win, monkeypatch, started):
    seen = []
    monkeypatch.setattr(
        dialogs,
        "ask_agent",
        lambda parent, project, last, shell=None: seen.append(last)
        or dialogs.StartChoice("codex", False),
    )
    select(win, "Tarkov")
    win._start()
    win._start()

    assert seen == ["claude", "codex"]


def test_the_chosen_shell_is_used_and_remembered(win, monkeypatch, started, tmp_path):
    seen = []
    monkeypatch.setattr(
        dialogs,
        "ask_agent",
        lambda parent, project, last, shell=None: seen.append(shell)
        or dialogs.StartChoice("claude", False, True, "powershell"),
    )
    select(win, "Tarkov")
    win._start()
    win._start()

    assert seen == ["cmd", "powershell"]
    assert started[-1] == ("Tarkov", "claude", "crt", False, "skip", "powershell")
    saved = json.loads((tmp_path / "config.json").read_text(encoding="utf-8"))
    assert saved["last_shell"] == "powershell"


def test_a_cancelled_dialog_changes_nothing(win, monkeypatch, started, tmp_path):
    monkeypatch.setattr(dialogs, "ask_agent", lambda parent, project, last, shell=None: None)
    select(win, "Tarkov")
    win._start()

    assert win.config.last_agent == "claude"
    assert not (tmp_path / "config.json").exists()


def test_a_new_project_also_asks(win, monkeypatch, started, demo_root):
    """'Neues Projekt' startet gleich im Anschluss - auch dort wird gefragt."""
    monkeypatch.setattr(dialogs, "ask_new_name", lambda parent: "Frisch")
    asked = []
    monkeypatch.setattr(
        dialogs,
        "ask_agent",
        lambda parent, project, last, shell=None: asked.append(project.name)
        or dialogs.StartChoice("claude", False),
    )
    win._new_project()

    assert asked == ["Frisch"]
    assert started == [("Frisch", "claude", "crt", False)]


def test_a_failing_start_is_reported(win, chooses, monkeypatch):
    """Fehlt der gewaehlte Agent im PATH, muss die Meldung ankommen."""
    chooses("codex")
    shown = []
    monkeypatch.setattr(dialogs, "show_error", lambda parent, message: shown.append(message))
    monkeypatch.setattr(
        runner,
        "start",
        lambda *a, **k: (_ for _ in ()).throw(runner.RunnerError("CODEX fehlt")),
    )
    select(win, "Tarkov")
    win._start()

    assert shown == ["CODEX fehlt"]


# --- Der zweite Start holt dieses Fenster nach vorn -------------------------


def test_present_brings_a_minimized_window_back(win):
    """Ein zweiter Start soll das vorhandene Fenster zeigen, auch wenn es
    in der Taskleiste liegt - sonst schiene der Klick wirkungslos."""
    win.showMinimized()
    assert win.isMinimized()

    win.present()
    assert not win.isMinimized()


def test_present_shows_a_hidden_window(win):
    win.hide()
    win.present()
    assert win.isVisible()


# --- Die Liste aktuell halten ----------------------------------------------


def shortcut_keys(win: MainWindow) -> set[str]:
    return {shortcut.key().toString() for shortcut in win.findChildren(QShortcut)}


def test_a_shortcut_rescans_the_folder(win, demo_root):
    """F5 startet, kann also nicht auch aktualisieren."""
    assert "Ctrl+R" in shortcut_keys(win)

    (demo_root / "Frisch").mkdir()
    assert "Frisch" not in visible_names(win)
    win._rescan()
    assert "Frisch" in visible_names(win)


def test_rescanning_keeps_the_selected_project(win, demo_root):
    select(win, "Tarkov")
    (demo_root / "Frisch").mkdir()
    win._rescan()
    assert win._selected().name == "Tarkov"


def test_coming_back_to_the_window_rescans(win, demo_root):
    """Ein Ordner, der im Explorer entsteht, war sonst erst nach der
    naechsten Aktion im Programm zu sehen."""
    (demo_root / "Frisch").mkdir()
    assert "Frisch" not in visible_names(win)

    QApplication.sendEvent(win, QEvent(QEvent.WindowActivate))
    assert "Frisch" in visible_names(win)


# --- Suche -----------------------------------------------------------------


def test_the_search_finds_a_project_type(win):
    win.search.setText("node")
    assert visible_names(win) == ["Gangland"]


def test_the_search_still_finds_names(win):
    win.search.setText("tark")
    assert visible_names(win) == ["Tarkov"]


# --- Zeilen und Spalten ----------------------------------------------------


def test_fit_pads_a_short_value_to_the_column_width():
    assert window_module.fit("py", 5) == "py   "


def test_fit_shortens_a_long_value_and_says_so():
    assert window_module.fit("abcdefgh", 5) == "abc… "


def test_fit_always_leaves_a_gap_to_the_next_column():
    """Ein Wert, der die Spalte genau ausfuellt, klebte sonst am naechsten:
    '...Projek…docs' war nicht mehr als zwei Spalten zu lesen."""
    assert window_module.fit("abcde", 5).endswith(" ")
    assert window_module.fit("abcdefgh", 5).endswith(" ")


def test_fit_leaves_the_last_column_alone():
    """Breite 0 heisst: diese Spalte bekommt den Rest."""
    assert window_module.fit("abcdefgh", 0) == "abcdefgh"


def test_the_row_uses_the_widths_from_the_column_table(win):
    """Zeile und Kopf gehen von denselben Breiten aus.

    Vorher standen die Zahlen zweimal da - in COLUMNS und noch einmal im
    Formatstring der Zeile. Wer eine aenderte, verschob still den Kopf.
    """
    row = row_of(win, "Gangland")
    after_name = len(window_module.ROW_PREFIX) + window_module.COLUMNS[0][2]
    assert row[after_name:].startswith("node")


def test_a_name_too_long_for_its_column_ends_in_an_ellipsis(win, demo_root):
    long_name = "Ein ausgesprochen langer Projektname der nicht hineinpasst"
    (demo_root / long_name).mkdir()
    win.refresh()

    row = row_of(win, long_name)
    after_name = len(window_module.ROW_PREFIX) + window_module.COLUMNS[0][2]
    assert row[:after_name].rstrip().endswith("…")


def test_a_shortened_name_is_still_readable_in_full(win, demo_root):
    """Das '…' sagt nur, dass gekuerzt wurde.

    Zwei Namen, die sich erst hinter dem Schnitt unterscheiden, sehen in
    der Liste weiterhin gleich aus - lesbar bleiben sie ueber den
    Mauszeiger, der den ganzen Pfad zeigt.
    """
    long_name = "Ein ausgesprochen langer Projektname der nicht hineinpasst"
    (demo_root / long_name).mkdir()
    win.refresh()

    item = win.list.item(visible_names(win).index(long_name))
    assert long_name in item.toolTip()


# --- Favoriten -------------------------------------------------------------


def row_of(win: MainWindow, name: str) -> str:
    return win.list.item(visible_names(win).index(name)).text()


def test_a_favorite_moves_to_the_top_of_the_list(win):
    select(win, "Tarkov")
    assert visible_names(win)[0] != "Tarkov"
    win._toggle_favorite()
    assert visible_names(win)[0] == "Tarkov"


def test_a_favorite_stays_on_top_after_sorting_by_name(win):
    select(win, "Tarkov")
    win._toggle_favorite()
    click_column(win, "name")
    assert visible_names(win)[0] == "Tarkov"


def test_a_favorite_wears_a_star_instead_of_the_arrow(win):
    select(win, "Tarkov")
    win._toggle_favorite()
    assert row_of(win, "Tarkov").startswith(window_module.FAVORITE_PREFIX)
    assert row_of(win, "Gangland").startswith(window_module.ROW_PREFIX)


def test_the_favorite_mark_is_as_wide_as_the_arrow(win):
    """Sonst stuenden die Spalten einer Favoritenzeile woanders.

    Gleich viele Zeichen genuegt dafuer nicht: der frueher benutzte Stern
    hatte deren genauso viele und mass trotzdem 13 px statt 7. Dass ein
    Zeichen aufs Raster passt, haelt `GRID_MARKS` fest - gemessen mit
    `tools/messe_zeichen.py`, siehe
    `test_every_marker_comes_from_the_measured_set`.
    """
    assert len(window_module.FAVORITE_PREFIX) == len(window_module.ROW_PREFIX)


def test_toggling_twice_removes_the_favorite(win):
    select(win, "Tarkov")
    win._toggle_favorite()
    win._toggle_favorite()
    assert win.config.favorites == []
    assert row_of(win, "Tarkov").startswith(window_module.ROW_PREFIX)


def test_a_favorite_is_written_to_the_config_file(win, tmp_path):
    select(win, "Tarkov")
    win._toggle_favorite()
    saved = json.loads((tmp_path / "config.json").read_text(encoding="utf-8"))
    assert saved["favorites"] == ["Tarkov"]


def test_the_project_stays_selected_after_toggling(win):
    select(win, "Tarkov")
    win._toggle_favorite()
    assert win._selected().name == "Tarkov"


def test_the_context_menu_offers_the_favorite(win):
    select(win, "Tarkov")
    labels = [action.text() for action in win._context_menu().actions()]
    assert any("Favorit" in label for label in labels)


def test_a_favorite_surviving_a_restart_is_still_on_top(win, demo_root, tmp_path):
    select(win, "Tarkov")
    win._toggle_favorite()

    config = Config.load(tmp_path / "config.json")
    config.projects_root = demo_root
    again = MainWindow(config, tmp_path / "config.json")
    assert visible_names(again)[0] == "Tarkov"


# --- Als Administrator ------------------------------------------------------


def test_a_ticked_admin_box_reaches_the_runner(win, monkeypatch, started):
    monkeypatch.setattr(
        dialogs,
        "ask_agent",
        lambda parent, project, last, shell=None: dialogs.StartChoice("claude", True),
    )
    select(win, "Tarkov")
    win._start()
    assert started == [("Tarkov", "claude", "crt", True)]


def test_a_ticked_skip_box_reaches_the_runner(win, monkeypatch, started):
    monkeypatch.setattr(
        dialogs,
        "ask_agent",
        lambda parent, project, last, shell=None: dialogs.StartChoice("claude", False, True),
    )
    select(win, "Tarkov")
    win._start()
    assert started == [("Tarkov", "claude", "crt", False, "skip")]


def test_an_untouched_admin_box_starts_plainly(win, chooses, started):
    chooses("codex")
    select(win, "Tarkov")
    win._start()
    assert started == [("Tarkov", "codex", "crt", False)]


def test_the_admin_choice_is_not_written_to_the_config(
    win, monkeypatch, started, tmp_path
):
    """Gemerkt wird nur der Agent. Ein stehengebliebenes Haekchen hiesse,
    dass jeder spaetere Start still einen UAC-Dialog aufmacht."""
    monkeypatch.setattr(
        dialogs,
        "ask_agent",
        lambda parent, project, last, shell=None: dialogs.StartChoice("codex", True),
    )
    select(win, "Tarkov")
    win._start()

    saved = json.loads((tmp_path / "config.json").read_text(encoding="utf-8"))
    assert saved["last_agent"] == "codex"
    assert not [key for key in saved if "admin" in key]


@pytest.fixture
def terminals(monkeypatch):
    """Faengt ab, womit `runner.open_terminal` aufgerufen wird."""
    calls = []
    monkeypatch.setattr(
        runner,
        "open_terminal",
        lambda project, style, admin=False: calls.append(
            (project.name, style, admin)
        ),
    )
    return calls


def test_the_terminal_can_be_opened_as_admin(win, terminals):
    select(win, "Gangland")
    win._open_terminal_admin()
    assert terminals == [("Gangland", "crt", True)]


def test_the_plain_terminal_stays_unelevated(win, terminals):
    select(win, "Gangland")
    win._open_terminal()
    assert terminals == [("Gangland", "crt", False)]


def test_shift_f4_opens_the_admin_terminal(win):
    """F4 oeffnet das Terminal, Shift+F4 dasselbe mit Rechten."""
    assert "Shift+F4" in shortcut_keys(win)


def test_the_context_menu_offers_the_admin_terminal(win):
    labels = [action.text() for action in win._context_menu().actions()]
    assert any("Administrator" in label for label in labels)


def test_a_refused_admin_terminal_is_reported(win, monkeypatch):
    """Klickt man im UAC-Dialog auf 'Nein', muss die Meldung ankommen."""
    shown = []
    monkeypatch.setattr(
        dialogs, "show_error", lambda parent, message: shown.append(message)
    )
    monkeypatch.setattr(
        runner,
        "open_terminal",
        lambda *a, **k: (_ for _ in ()).throw(runner.RunnerError("abgelehnt")),
    )
    select(win, "Gangland")
    win._open_terminal_admin()

    assert shown == ["abgelehnt"]


# --- Die Notizspalte -------------------------------------------------------


@pytest.fixture
def notepad(monkeypatch):
    """Faengt ab, was `open_note` starten wuerde - nichts geht wirklich auf."""
    calls = []
    monkeypatch.setattr(
        runner, "_spawn", lambda args, cwd, console=True: calls.append((args, cwd))
    )
    return calls


def cell_of(win: MainWindow, name: str, key: str) -> str:
    """Der Inhalt einer Spalte in der Zeile von `name`, ohne Auffuellung."""
    row = row_of(win, name)
    start = len(window_module.ROW_PREFIX)
    for column_key, _title, width in window_module.COLUMNS:
        end = start + width if width else len(row)
        if column_key == key:
            return row[start:end].strip()
        start = end
    raise AssertionError(f"Spalte '{key}' gibt es nicht")


def test_a_project_without_a_note_shows_the_empty_mark(win):
    assert cell_of(win, "Gangland", "has_note") == window_module.NO_NOTE_MARK


def test_a_project_with_a_note_shows_the_note_mark(win, demo_root):
    (demo_root / "Gangland" / NOTE_NAME).write_text("# Aufgaben", encoding="utf-8")
    win.refresh()
    assert cell_of(win, "Gangland", "has_note") == window_module.NOTE_MARK


def test_opening_the_note_creates_it_and_the_mark_appears(win, demo_root, notepad):
    select(win, "Gangland")
    win._open_note()
    assert (demo_root / "Gangland" / NOTE_NAME).is_file()
    assert cell_of(win, "Gangland", "has_note") == window_module.NOTE_MARK


def test_opening_the_note_keeps_the_project_selected(win, notepad):
    select(win, "Gangland")
    win._open_note()
    assert win._selected().name == "Gangland"


def test_a_shortcut_opens_the_note(win):
    assert "F6" in shortcut_keys(win)


def test_the_context_menu_offers_the_note(win):
    select(win, "Gangland")
    labels = [action.text() for action in win._context_menu().actions()]
    assert any("Aufgaben" in label for label in labels)


def test_opening_the_note_without_a_selection_is_reported(win, monkeypatch, notepad):
    shown = []
    monkeypatch.setattr(
        dialogs, "show_error", lambda parent, message: shown.append(message)
    )
    win.list.setCurrentRow(-1)
    win._open_note()
    assert shown and notepad == []


# --- Ein Klick trifft die Spalte, ueber der er steht -----------------------


def x_of_column(win: MainWindow, key: str, character: int = 0) -> int:
    """Die x-Position des `character`-ten Zeichens der Spalte `key`.

    Gerechnet in Koordinaten des Listeninhalts, so wie sie ein Mausklick
    liefert - also ohne den Rahmen, aber mit Rand und Innenabstand.
    """
    from projecthq.theme import ROW_MARKER, ROW_PADDING

    metrics = win.list.fontMetrics()
    start = ROW_MARKER + ROW_PADDING + metrics.horizontalAdvance(
        window_module.ROW_PREFIX
    )
    for column_key, _title, width in window_module.COLUMNS:
        if column_key == key:
            break
        start += metrics.horizontalAdvance("0" * width)
    return start + metrics.horizontalAdvance("0") * character + 1


def test_a_click_finds_the_column_it_points_at(win):
    for key, _title, _width in window_module.COLUMNS:
        assert win._column_at(x_of_column(win, key)) == key


def test_a_click_still_finds_the_column_at_its_last_character(win):
    """Die Spalte reicht bis an ihre letzte Stelle - sonst laege ein Teil
    der Trefferzone bereits ueber der naechsten Spalte."""
    for key, _title, width in window_module.COLUMNS:
        if width:
            assert win._column_at(x_of_column(win, key, width - 1)) == key


def test_a_click_on_the_prefix_belongs_to_no_column(win):
    """Links vom Pfeil faengt keine Spalte an - dort darf nichts aufgehen."""
    assert win._column_at(0) is None


def test_the_last_column_reaches_to_the_right_edge(win):
    """Ihre Breite steht als 0 in der Tabelle: sie bekommt den Rest."""
    last_key = window_module.COLUMNS[-1][0]
    assert win._column_at(x_of_column(win, last_key, 400)) == last_key


def test_clicking_the_note_column_opens_the_note(win, demo_root, notepad):
    select(win, "Gangland")
    win._on_cell_clicked(win.list.currentItem(), x_of_column(win, "has_note"))
    assert (demo_root / "Gangland" / NOTE_NAME).is_file()
    (args, _cwd), = notepad
    assert args[0] == "notepad"


def test_clicking_another_column_opens_nothing(win, demo_root, notepad):
    select(win, "Gangland")
    win._on_cell_clicked(win.list.currentItem(), x_of_column(win, "name"))
    assert notepad == []
    assert not (demo_root / "Gangland" / NOTE_NAME).exists()


def test_a_click_opens_the_note_of_the_row_it_hit(win, demo_root, notepad):
    """Geoeffnet wird die Zeile unter dem Zeiger, nicht die zuletzt
    ausgewaehlte - sonst oeffnete der erste Klick das falsche Projekt."""
    select(win, "Gangland")
    item = win.list.item(visible_names(win).index("Tarkov"))
    win._on_cell_clicked(item, x_of_column(win, "has_note"))
    assert (demo_root / "Tarkov" / NOTE_NAME).is_file()
    assert not (demo_root / "Gangland" / NOTE_NAME).exists()


# --- Die Agentenspalte -----------------------------------------------------


def test_a_project_never_started_shows_a_dash(win):
    assert cell_of(win, "Gangland", "agent") == window_module.NO_AGENT_MARK


def test_the_column_shows_the_agent_after_a_start(win, chooses, started):
    chooses("codex")
    select(win, "Tarkov")
    win._start()
    assert cell_of(win, "Tarkov", "agent") == AGENT_MARKS["codex"] + " CODEX"


def test_each_project_keeps_its_own_agent(win, chooses, started):
    chooses("codex")
    select(win, "Tarkov")
    win._start()
    chooses("claude")
    select(win, "Gangland")
    win._start()

    assert cell_of(win, "Tarkov", "agent") == AGENT_MARKS["codex"] + " CODEX"
    assert cell_of(win, "Gangland", "agent") == AGENT_MARKS["claude"] + " CLAUDE"


def test_the_agent_is_written_to_the_config_file(win, chooses, started, tmp_path):
    chooses("codex")
    select(win, "Tarkov")
    win._start()
    saved = json.loads((tmp_path / "config.json").read_text(encoding="utf-8"))
    assert saved["project_agents"] == {"Tarkov": "codex"}


def test_the_agent_survives_a_restart(win, chooses, started, demo_root, tmp_path):
    chooses("codex")
    select(win, "Tarkov")
    win._start()

    config = Config.load(tmp_path / "config.json")
    config.projects_root = demo_root
    again = MainWindow(config, tmp_path / "config.json")
    assert cell_of(again, "Tarkov", "agent") == AGENT_MARKS["codex"] + " CODEX"


def test_a_failed_start_remembers_no_agent(win, chooses, monkeypatch):
    """Sonst stuende in der Spalte, womit nie gearbeitet wurde."""

    def kaputt(*args, **kwargs):
        raise runner.RunnerError("kaputt")

    monkeypatch.setattr(dialogs, "show_error", lambda parent, message: None)
    monkeypatch.setattr(runner, "start", kaputt)
    chooses("codex")
    select(win, "Tarkov")
    win._start()
    assert cell_of(win, "Tarkov", "agent") == window_module.NO_AGENT_MARK


def test_a_renamed_project_keeps_its_agent(win, chooses, started, monkeypatch):
    chooses("codex")
    select(win, "Tarkov")
    win._start()

    monkeypatch.setattr(dialogs, "ask_rename", lambda parent, project: "Tarkov2")
    select(win, "Tarkov")
    win._rename()
    assert cell_of(win, "Tarkov2", "agent") == AGENT_MARKS["codex"] + " CODEX"


def test_the_agent_column_can_be_sorted(win, chooses, started):
    chooses("codex")
    select(win, "Tarkov")
    win._start()
    click_column(win, "agent")
    assert visible_names(win)[0] == "Tarkov"


def test_the_note_column_can_be_sorted(win, demo_root):
    (demo_root / "Tarkov" / NOTE_NAME).write_text("x", encoding="utf-8")
    win.refresh()
    click_column(win, "has_note")
    assert visible_names(win)[0] == "Tarkov"


# --- Jedes Zeichen der Liste muss auf das Raster passen -------------------


def markers_in_use() -> dict[str, str]:
    """Alle Symbole, die tatsaechlich in einer Listenzeile landen."""
    return {
        "Pfeil": window_module.ROW_PREFIX.strip(),
        "Favorit": window_module.FAVORITE_PREFIX.strip(),
        "Notiz": window_module.NOTE_MARK,
        "keine Notiz": window_module.NO_NOTE_MARK,
        "kein Agent": window_module.NO_AGENT_MARK,
        **{"Agent " + a: m for a, m in AGENT_MARKS.items()},
    }


def test_every_marker_comes_from_the_measured_set():
    """Die Spalten stehen auf einem Raster aus gleich breiten Zeichen.

    Nachmessen kann dieser Test nicht: die Suite laeuft offscreen, und
    ohne Schriftdatenbank meldet Qt fuer jedes Zeichen dieselbe Breite -
    auch fuer den frueher benutzten Stern, der in Wirklichkeit 13 px statt
    7 mass und die Favoritenzeile verschob. Gemessen wird mit
    `tools/messe_zeichen.py` auf einem richtigen Bildschirm; hier wird nur
    festgehalten, dass kein Symbol an der Messung vorbei hereinkommt.
    """
    fremd = {
        name: zeichen
        for name, zeichen in markers_in_use().items()
        if zeichen not in window_module.GRID_MARKS
    }
    assert not fremd, (
        f"ungemessene Zeichen: {fremd} - erst mit tools/messe_zeichen.py "
        "pruefen, dann in GRID_MARKS aufnehmen"
    )


def test_the_star_that_broke_the_grid_stays_out():
    """Damit niemand ihn aus Versehen zurueckholt."""
    assert "★" not in window_module.GRID_MARKS


def test_the_column_head_starts_where_the_rows_do(win):
    """Der Kopf ruecken um den Pfeil ein, die Zeilen tragen ihn - beide
    muessen bei derselben Stelle landen.

    `_size_columns` wird zuerst gerufen: im `__init__` lief es, bevor das
    Stylesheet die endgueltige Schrift gesetzt hat - deshalb tut es das
    `showEvent` noch einmal. Ohne den Aufruf haenge dieser Test daran, ob
    ein frueherer Test das Fenster schon gezeigt hat.
    """
    win._size_columns()
    metrics = win.list.fontMetrics()
    assert win._column_spacer.width() == metrics.horizontalAdvance(
        window_module.ROW_PREFIX
    )


#: Wie viele Zeichen bei der Startbreite von 980 px in eine Zeile passen.
#: Gerechnet mit der Grundbreite 7 px von Consolas 13 px, abzueglich
#: Fensterrahmen, Rand und Innenabstand einer Zeile. In Pixeln laesst sich
#: das hier nicht pruefen, siehe oben.
LINE_BUDGET = 130


def test_the_columns_leave_room_for_the_last_one(win):
    """Zwei Spalten mehr duerfen BEARBEITET nicht aus dem Fenster schieben.

    Die letzte Spalte hat die Breite 0 und bekommt den Rest - ist der
    Rest zu klein, steht dort ein abgeschnittenes Datum.
    """
    fest = len(window_module.ROW_PREFIX) + sum(
        width for _key, _title, width in window_module.COLUMNS
    )
    rest = LINE_BUDGET - fest
    assert rest >= len("00.00.0000") + 2, f"nur {rest} Zeichen fuer die letzte Spalte"


def test_only_the_last_column_may_have_no_width():
    """Breite 0 heisst 'bekommt den Rest'. Steht sie woanders, verschluckt
    diese Spalte alle dahinter."""
    widths = [width for _key, _title, width in window_module.COLUMNS]
    assert all(widths[:-1]), "nur die letzte Spalte darf die Breite 0 haben"


# --- Ein Doppelklick auf die Notizspalte startet nicht --------------------


def test_a_double_click_starts_the_project(win, started, chooses):
    """Der gewohnte Weg bleibt: Doppelklick irgendwo auf die Zeile."""
    chooses("claude")
    item = win.list.item(visible_names(win).index("Gangland"))
    win._on_cell_double_clicked(item, x_of_column(win, "name"))
    assert [name for name, *_rest in started] == ["Gangland"]


def test_a_double_click_on_the_note_column_starts_nothing(win, started, notepad):
    """Sonst ginge aus einer Geste beides auf: die Notiz und der
    Startdialog. Wer auf das Symbol zielt, meint die Notiz."""
    item = win.list.item(visible_names(win).index("Gangland"))
    win._on_cell_double_clicked(item, x_of_column(win, "has_note"))
    assert started == []


def test_a_double_click_takes_the_row_it_hit(win, started, chooses):
    """Nicht die zuletzt ausgewaehlte - sonst startete der Doppelklick auf
    ein anderes Projekt das vorherige."""
    chooses("claude")
    select(win, "Gangland")
    item = win.list.item(visible_names(win).index("Tarkov"))
    win._on_cell_double_clicked(item, x_of_column(win, "name"))
    assert [name for name, *_rest in started] == ["Tarkov"]


# --- "Stand einfuegen" ----------------------------------------------------


@pytest.fixture
def fester_stand(monkeypatch):
    """Die echte Standerhebung liest die Sitzungsarchive des pruefenden
    Rechners. Davon darf kein Test abhaengen."""
    monkeypatch.setattr(
        runner.activity, "status_block", lambda pfad: "## Stand vom HEUTE\n\n- etwas\n"
    )


def test_the_context_menu_offers_the_status(win, fester_stand):
    select(win, "Gangland")
    labels = [action.text() for action in win._context_menu().actions()]
    assert any("Stand" in label for label in labels)


def test_inserting_a_status_writes_the_note(win, demo_root, notepad, fester_stand):
    select(win, "Gangland")
    win._insert_status()
    text = (demo_root / "Gangland" / NOTE_NAME).read_text(encoding="utf-8")
    assert "## Stand vom HEUTE" in text


def test_inserting_a_status_makes_the_mark_appear(win, notepad, fester_stand):
    select(win, "Gangland")
    assert cell_of(win, "Gangland", "has_note") == window_module.NO_NOTE_MARK
    win._insert_status()
    assert cell_of(win, "Gangland", "has_note") == window_module.NOTE_MARK


def test_inserting_a_status_keeps_the_selection(win, notepad, fester_stand):
    select(win, "Gangland")
    win._insert_status()
    assert win._selected().name == "Gangland"


def test_inserting_without_a_selection_is_reported(win, monkeypatch, notepad, fester_stand):
    shown = []
    monkeypatch.setattr(
        dialogs, "show_error", lambda parent, message: shown.append(message)
    )
    win.list.setCurrentRow(-1)
    win._insert_status()
    assert shown and notepad == []


def test_a_failing_status_is_reported_not_crashed(win, monkeypatch, notepad):
    """Der Ordner ist weg, waehrend das Menue offen stand."""
    shown = []
    monkeypatch.setattr(
        dialogs, "show_error", lambda parent, message: shown.append(message)
    )

    def kaputt(project):
        raise runner.RunnerError("Ordner ist weg")

    monkeypatch.setattr(runner, "insert_status", kaputt)
    select(win, "Gangland")
    win._insert_status()
    assert shown == ["Ordner ist weg"]


def test_a_created_note_is_not_empty_anymore(win, demo_root, notepad, fester_stand):
    """Die urspruengliche Beschwerde: erst kam ein leeres Blatt."""
    select(win, "Gangland")
    win._open_note()
    text = (demo_root / "Gangland" / NOTE_NAME).read_text(encoding="utf-8")
    assert "## Stand vom HEUTE" in text


# --- Datum und Agent kommen aus dem Zwischenspeicher ----------------------


def datei_in(projekt: Path, rel: str, wann: float | None = None) -> Path:
    """Legt eine Datei an und setzt notfalls ihre Zeit."""
    ziel = projekt / rel
    ziel.parent.mkdir(parents=True, exist_ok=True)
    ziel.write_text("x", encoding="utf-8")
    if wann is not None:
        os.utime(ziel, (wann, wann))
    return ziel


def test_a_change_deep_inside_shows_up_in_the_date(win, demo_root):
    """Der Kern: die Ordnerzeit merkt nichts davon.

    Gemessen an 'Webshop': Ordner 02.08., juengste Datei
    07.09. - und weil die Liste danach sortiert, stand das Projekt ganz
    unten, waehrend darin getippt wurde.
    """
    ordner = demo_root / "Gangland"
    zukunft = time.time() + 3600
    datei_in(ordner, "src/tief/datei.js", zukunft)
    alt = time.time() - 60 * 86400
    os.utime(ordner, (alt, alt))

    win._reload()
    assert cell_of(win, "Gangland", "mtime") == time.strftime(
        "%d.%m.%Y", time.localtime(zukunft)
    )


def test_the_freshest_project_sorts_to_the_top(win, demo_root):
    """Die eigentliche Wirkung: Vorgabe ist BEARBEITET absteigend."""
    ordner = demo_root / "Gangland"
    datei_in(ordner, "src/tief/datei.js", time.time() + 3600)
    alt = time.time() - 60 * 86400
    os.utime(ordner, (alt, alt))

    win._reload()
    assert visible_names(win)[0] == "Gangland"


@pytest.fixture
def durchlaeufe(monkeypatch):
    """Zaehlt die teure Suche nach der juengsten Datei - nicht den Aufruf
    des Getters, der ja gerade den gemerkten Wert zurueckgeben soll."""
    gezaehlt = []
    echt = runner.activity.newest_change
    monkeypatch.setattr(
        runner.activity,
        "newest_change",
        lambda pfad, **kw: (gezaehlt.append(pfad), echt(pfad, **kw))[1],
    )
    return gezaehlt


def test_returning_to_the_window_does_not_recompute(win, demo_root, durchlaeufe):
    """Sonst kostete jedes Alt-Tab rund 300 ms. Gerechnet wird beim Start
    und bei Strg+R."""
    win._rescan()
    win._rescan()
    assert durchlaeufe == [], "der gemerkte Wert soll gelten"


def test_a_reload_looks_again(win, demo_root, durchlaeufe):
    win._reload()
    assert durchlaeufe, "Strg+R soll neu rechnen"


def test_ctrl_r_is_still_the_shortcut(win):
    assert "Ctrl+R" in shortcut_keys(win)


def test_a_project_appearing_meanwhile_gets_its_real_date(win, demo_root):
    """Ein Ordner, der nebenher im Explorer entsteht, war noch nie im
    Zwischenspeicher - er wird berechnet, ohne dass jemand Strg+R
    druecken muss."""
    frisch = demo_root / "Frisch"
    frisch.mkdir()
    datei_in(frisch, "tief/x.txt", time.time() + 3600)
    alt = time.time() - 60 * 86400
    os.utime(frisch, (alt, alt))

    win._rescan()
    assert cell_of(win, "Frisch", "mtime") != time.strftime(
        "%d.%m.%Y", time.localtime(alt)
    )


def test_starting_a_project_marks_it_edited_even_without_a_file_change(
    win, demo_root, chooses, started
):
    """Ein Start zaehlt als Aktivitaet, auch wenn dabei keine Datei im
    Ordner angefasst wird - Claude kann eine Weile antworten, ohne etwas
    zu schreiben, und BEARBEITET soll trotzdem den heutigen Tag zeigen."""
    ordner = demo_root / "Gangland"
    alt = time.time() - 60 * 86400
    os.utime(ordner, (alt, alt))
    for datei in ordner.rglob("*"):
        if datei.is_file():
            os.utime(datei, (alt, alt))

    chooses("claude")
    select(win, "Gangland")
    win._start()

    assert cell_of(win, "Gangland", "mtime") == time.strftime(
        "%d.%m.%Y", time.localtime()
    )


def test_the_start_time_survives_a_restart(win, demo_root, chooses, started, tmp_path):
    ordner = demo_root / "Gangland"
    alt = time.time() - 60 * 86400
    os.utime(ordner, (alt, alt))
    for datei in ordner.rglob("*"):
        if datei.is_file():
            os.utime(datei, (alt, alt))

    chooses("claude")
    select(win, "Gangland")
    win._start()

    neu = MainWindow(Config.load(tmp_path / "config.json"), tmp_path / "config.json")
    assert cell_of(neu, "Gangland", "mtime") == time.strftime(
        "%d.%m.%Y", time.localtime()
    )


# --- Die Agentenspalte kommt aus den Sitzungen ----------------------------


def test_the_agent_comes_from_the_session_archive(win, demo_root, tmp_path, monkeypatch):
    """Womit im Ordner gearbeitet wurde - nicht nur, was HQ gestartet hat.

    Genau die Beschwerde: in HQ lief Claude, die Spalte zeigte '-'.
    """
    claude = tmp_path / "claude" / "projects"
    ordner = claude / runner.activity.claude_folder_name(demo_root / "Gangland")
    ordner.mkdir(parents=True)
    (ordner / "s.jsonl").write_text(
        json.dumps({"type": "system", "cwd": str(demo_root / "Gangland")}),
        encoding="utf-8",
    )
    monkeypatch.setattr(runner.activity, "CLAUDE_ROOT", claude)
    monkeypatch.setattr(runner.activity, "CODEX_ROOT", tmp_path / "leer")

    win._reload()
    assert cell_of(win, "Gangland", "agent") == AGENT_MARKS["claude"] + " CLAUDE"


def test_a_recorded_start_fills_the_gap(win, chooses, started, tmp_path, monkeypatch):
    """Ohne Sitzung im Archiv gilt weiter, was HQ selbst mitgeschrieben
    hat - etwa wenn ein altes Transkript weggeraeumt wurde."""
    monkeypatch.setattr(runner.activity, "CLAUDE_ROOT", tmp_path / "leer")
    monkeypatch.setattr(runner.activity, "CODEX_ROOT", tmp_path / "leer2")
    chooses("codex")
    select(win, "Tarkov")
    win._start()
    assert cell_of(win, "Tarkov", "agent") == AGENT_MARKS["codex"] + " CODEX"


def test_a_project_with_neither_still_shows_a_dash(win, tmp_path, monkeypatch):
    monkeypatch.setattr(runner.activity, "CLAUDE_ROOT", tmp_path / "leer")
    monkeypatch.setattr(runner.activity, "CODEX_ROOT", tmp_path / "leer2")
    win._reload()
    assert cell_of(win, "Gangland", "agent") == window_module.NO_AGENT_MARK


# --- Automatischer Shutdown --------------------------------------------


@pytest.fixture
def shutdown_calls(monkeypatch):
    """Faengt ab, was der Runner an Windows uebergeben wuerde - kein Test
    darf den pruefenden Rechner wirklich herunterfahren."""
    calls = []
    monkeypatch.setattr(
        runner, "schedule_shutdown", lambda minutes: calls.append(("schedule", minutes))
    )
    monkeypatch.setattr(runner, "cancel_shutdown", lambda: calls.append(("cancel",)))
    return calls


def test_shutdown_schedules_and_reddens_the_button(win, monkeypatch, shutdown_calls):
    monkeypatch.setattr(dialogs, "ask_shutdown_minutes", lambda parent: 30)
    win._on_shutdown_clicked()
    assert shutdown_calls == [("schedule", 30)]
    assert win.shutdown_button.objectName() == "danger"
    assert win.config.shutdown_at > time.time()


def test_a_cancelled_dropdown_schedules_nothing(win, monkeypatch, shutdown_calls):
    monkeypatch.setattr(dialogs, "ask_shutdown_minutes", lambda parent: None)
    win._on_shutdown_clicked()
    assert shutdown_calls == []
    assert win.config.shutdown_at == 0.0
    assert win.shutdown_button.objectName() != "danger"


def test_clicking_the_active_button_asks_before_cancelling(win, monkeypatch, shutdown_calls):
    monkeypatch.setattr(dialogs, "ask_shutdown_minutes", lambda parent: 15)
    win._on_shutdown_clicked()

    monkeypatch.setattr(dialogs, "confirm_cancel_shutdown", lambda parent, when: False)
    win._on_shutdown_clicked()

    assert shutdown_calls == [("schedule", 15)]
    assert win.config.shutdown_at > time.time()
    assert win.shutdown_button.objectName() == "danger"


def test_confirming_cancel_stops_the_shutdown(win, monkeypatch, shutdown_calls):
    monkeypatch.setattr(dialogs, "ask_shutdown_minutes", lambda parent: 15)
    win._on_shutdown_clicked()

    monkeypatch.setattr(dialogs, "confirm_cancel_shutdown", lambda parent, when: True)
    win._on_shutdown_clicked()

    assert shutdown_calls == [("schedule", 15), ("cancel",)]
    assert win.config.shutdown_at == 0.0
    assert win.shutdown_button.objectName() != "danger"


def test_the_status_line_shows_the_countdown_while_active(win, monkeypatch, shutdown_calls):
    monkeypatch.setattr(dialogs, "ask_shutdown_minutes", lambda parent: 15)
    win._on_shutdown_clicked()
    assert "Verbleibend" in win.status.text()


def test_the_status_line_returns_to_the_path_after_cancelling(
    win, monkeypatch, shutdown_calls
):
    select(win, "Gangland")
    monkeypatch.setattr(dialogs, "ask_shutdown_minutes", lambda parent: 15)
    win._on_shutdown_clicked()

    monkeypatch.setattr(dialogs, "confirm_cancel_shutdown", lambda parent, when: True)
    win._on_shutdown_clicked()

    assert "Gangland" in win.status.text()


def test_a_scheduled_shutdown_is_shown_again_after_a_restart(
    win, monkeypatch, shutdown_calls, demo_root, tmp_path
):
    monkeypatch.setattr(dialogs, "ask_shutdown_minutes", lambda parent: 15)
    win._on_shutdown_clicked()

    config = Config.load(tmp_path / "config.json")
    config.projects_root = demo_root
    again = MainWindow(config, tmp_path / "config.json")
    assert again.shutdown_button.objectName() == "danger"
