"""Was in einem Projekt zuletzt geschehen ist.

Die Sitzungsdateien von Claude und Codex sind ein undokumentiertes
Format. Die Tests bauen sie deshalb nach, wie sie am 07.09.2026
tatsaechlich aussahen - inklusive der Eigenheit, dass beide ohne
Leerzeichen zwischen den Feldern schreiben.

Wichtiger als jedes einzelne Feld ist, dass **nichts** von hier eine
Ausnahme nach oben durchlaesst: die Notiz soll auch dann aufgehen, wenn
sich das Format morgen aendert.
"""

from __future__ import annotations

import json
import os
import subprocess
import time
from pathlib import Path

import pytest

from projecthq import activity


# --- Sitzungsdateien nachbauen --------------------------------------------


def claude_session(
    ordner: Path,
    name: str,
    cwd: str,
    titel: str | None = None,
    prompts: tuple[str, ...] = (),
    alter: float = 0.0,
) -> Path:
    """Eine Claude-Sitzung, wie sie wirklich aussieht."""
    ordner.mkdir(parents=True, exist_ok=True)
    zeilen = [{"type": "system", "cwd": cwd}]
    for text in prompts:
        zeilen.append({"type": "user", "message": {"role": "user", "content": text}})
    if titel is not None:
        zeilen.append({"type": "ai-title", "aiTitle": titel})
    datei = ordner / f"{name}.jsonl"
    datei.write_text(
        "\n".join(json.dumps(z, ensure_ascii=False, separators=(",", ":")) for z in zeilen),
        encoding="utf-8",
    )
    if alter:
        alt = time.time() - alter
        os.utime(datei, (alt, alt))
    return datei


def codex_session(
    wurzel: Path,
    name: str,
    cwd: str,
    prompts: tuple[str, ...] = (),
    alter: float = 0.0,
    *,
    old_format: bool = False,
) -> Path:
    """Eine Codex-Sitzung: der Ordner steht im Kopfsatz, nicht im Pfad.

    `old_format` baut die aeltere Form nach. Codex hat sein Protokoll
    zwischen Mai und September 2026 umgestellt, und beide Formen liegen
    nebeneinander im Archiv - gemessen an den 99 Sitzungen auf diesem
    Rechner.
    """
    wurzel.mkdir(parents=True, exist_ok=True)
    zeilen = [{"type": "session_meta", "payload": {"cwd": cwd}}]
    for text in prompts:
        if old_format:
            zeilen.append(
                {
                    "type": "response_item",
                    "payload": {
                        "type": "message",
                        "role": "user",
                        "content": [{"type": "input_text", "text": text}],
                    },
                }
            )
        else:
            zeilen.append(
                {
                    "type": "event_msg",
                    "payload": {
                        "type": "item_completed",
                        "item": {"type": "UserMessage", "text": text},
                    },
                }
            )
    datei = wurzel / f"rollout-{name}.jsonl"
    datei.write_text(
        "\n".join(json.dumps(z, ensure_ascii=False, separators=(",", ":")) for z in zeilen),
        encoding="utf-8",
    )
    if alter:
        alt = time.time() - alter
        os.utime(datei, (alt, alt))
    return datei


@pytest.fixture
def projekt(tmp_path: Path) -> Path:
    p = tmp_path / "projekte" / "Tarkov"
    p.mkdir(parents=True)
    return p


@pytest.fixture
def archive(tmp_path, monkeypatch) -> tuple[Path, Path]:
    """Legt die Sitzungsarchive auf tmp_path statt ins Benutzerprofil."""
    claude = tmp_path / "claude" / "projects"
    codex = tmp_path / "codex" / "sessions"
    claude.mkdir(parents=True)
    codex.mkdir(parents=True)
    monkeypatch.setattr(activity, "CLAUDE_ROOT", claude)
    monkeypatch.setattr(activity, "CODEX_ROOT", codex)
    return claude, codex


# --- Claude ---------------------------------------------------------------


def test_a_project_without_any_session_reports_nothing(projekt, archive):
    assert activity.claude_sessions(projekt) == []


def test_the_ai_title_becomes_the_topic(projekt, archive):
    claude, _codex = archive
    claude_session(
        claude / activity.claude_folder_name(projekt),
        "s1",
        str(projekt),
        titel="Admin-Startoptionen",
    )
    (eintrag,) = activity.claude_sessions(projekt)
    assert eintrag.what == "Admin-Startoptionen"
    assert eintrag.source == "Claude"


def test_without_a_title_the_first_prompt_is_used(projekt, archive):
    """Eine ganz frische Sitzung hat noch keinen Titel."""
    claude, _codex = archive
    claude_session(
        claude / activity.claude_folder_name(projekt),
        "s1",
        str(projekt),
        prompts=("mach mal die Spalten breiter", "und noch was"),
    )
    (eintrag,) = activity.claude_sessions(projekt)
    assert eintrag.what == "mach mal die Spalten breiter"


def test_injected_reminders_are_not_mistaken_for_a_prompt(projekt, archive):
    """Was das Werkzeug selbst einspeist, hat der Nutzer nicht geschrieben."""
    claude, _codex = archive
    claude_session(
        claude / activity.claude_folder_name(projekt),
        "s1",
        str(projekt),
        prompts=("<system-reminder>bla</system-reminder>", "die echte Frage"),
    )
    (eintrag,) = activity.claude_sessions(projekt)
    assert eintrag.what == "die echte Frage"


def test_a_folder_belonging_to_another_project_is_skipped(projekt, archive):
    """Der Ordnername wird aus dem Pfad gebaut - zwei Projekte koennen
    denselben Namen ergeben. Entschieden wird deshalb am mitgeschriebenen
    Arbeitsverzeichnis."""
    claude, _codex = archive
    claude_session(
        claude / activity.claude_folder_name(projekt),
        "s1",
        r"D:\ganz\woanders",
        titel="fremd",
    )
    assert activity.claude_sessions(projekt) == []


def test_sessions_come_back_newest_first(projekt, archive):
    claude, _codex = archive
    ordner = claude / activity.claude_folder_name(projekt)
    claude_session(ordner, "alt", str(projekt), titel="alt", alter=7200)
    claude_session(ordner, "neu", str(projekt), titel="neu", alter=60)
    assert [e.what for e in activity.claude_sessions(projekt)] == ["neu", "alt"]


def test_only_the_newest_sessions_are_reported(projekt, archive):
    claude, _codex = archive
    ordner = claude / activity.claude_folder_name(projekt)
    for i in range(6):
        claude_session(ordner, f"s{i}", str(projekt), titel=f"t{i}", alter=i * 60)
    assert len(activity.claude_sessions(projekt, limit=3)) == 3


def test_a_corrupt_session_file_is_simply_skipped(projekt, archive):
    """Kein Grund, die Notiz platzen zu lassen."""
    claude, _codex = archive
    ordner = claude / activity.claude_folder_name(projekt)
    ordner.mkdir(parents=True)
    (ordner / "kaputt.jsonl").write_text("{ das ist kein json", encoding="utf-8")
    claude_session(ordner, "heil", str(projekt), titel="heil")
    assert [e.what for e in activity.claude_sessions(projekt)] == ["heil"]


def test_a_missing_archive_is_not_an_error(projekt, tmp_path, monkeypatch):
    monkeypatch.setattr(activity, "CLAUDE_ROOT", tmp_path / "gibtsnicht")
    assert activity.claude_sessions(projekt) == []


# --- Codex ----------------------------------------------------------------


def test_codex_sessions_are_found_by_their_working_directory(projekt, archive):
    """Codex legt nach Datum ab, nicht nach Projekt - der Ordner steht im
    Kopfsatz jeder Datei."""
    _claude, codex = archive
    codex_session(
        codex / "2026" / "09" / "06",
        "a",
        str(projekt),
        prompts=("warum nur 80 fps",),
    )
    codex_session(
        codex / "2026" / "09" / "06", "b", r"D:\anderes", prompts=("egal",)
    )
    (eintrag,) = activity.codex_sessions(projekt)
    assert eintrag.what == "warum nur 80 fps"
    assert eintrag.source == "Codex"


def test_a_codex_session_without_a_prompt_is_skipped(projekt, archive):
    _claude, codex = archive
    codex_session(codex / "2026" / "09" / "06", "a", str(projekt))
    assert activity.codex_sessions(projekt) == []


def test_the_older_codex_format_is_read_too(projekt, archive):
    """Codex hat sein Protokoll umgestellt; die alten Sitzungen liegen
    weiter im Archiv. Wer nur die neue Form liest, sieht bei aelteren
    Projekten nichts - gemessen an 'Notizen', 13 Sitzungen, alle alt."""
    _claude, codex = archive
    codex_session(
        codex / "2026" / "05",
        "alt",
        str(projekt),
        prompts=("die kategorien passen nicht ins raster",),
        old_format=True,
    )
    (eintrag,) = activity.codex_sessions(projekt)
    assert eintrag.what == "die kategorien passen nicht ins raster"


def test_the_environment_block_is_not_mistaken_for_a_prompt(projekt, archive):
    """Die alte Form schiebt einen <environment_context> als erste
    Nutzernachricht voran."""
    _claude, codex = archive
    codex_session(
        codex / "2026" / "05",
        "alt",
        str(projekt),
        prompts=(
            "<environment_context>\n  <cwd>irgendwas</cwd>\n</environment_context>",
            "die echte Frage",
        ),
        old_format=True,
    )
    (eintrag,) = activity.codex_sessions(projekt)
    assert eintrag.what == "die echte Frage"


def test_codex_matching_ignores_upper_and_lower_case(projekt, archive):
    _claude, codex = archive
    codex_session(
        codex / "2026", "a", str(projekt).upper(), prompts=("trotzdem meins",)
    )
    assert len(activity.codex_sessions(projekt)) == 1


# --- Beide zusammen -------------------------------------------------------


def test_both_agents_appear_in_one_list_newest_first(projekt, archive):
    claude, codex = archive
    claude_session(
        claude / activity.claude_folder_name(projekt),
        "c",
        str(projekt),
        titel="mit Claude",
        alter=3600,
    )
    codex_session(
        codex / "2026", "x", str(projekt), prompts=("mit Codex",), alter=60
    )
    ergebnis = activity.sessions(projekt)
    assert [e.source for e in ergebnis] == ["Codex", "Claude"]


# --- Git ------------------------------------------------------------------


def git_repo(pfad: Path) -> Path:
    """Ein winziges Repository. Ohne Signatur und ohne Hooks, damit die
    Einstellungen des pruefenden Rechners nicht hineinreden."""
    pfad.mkdir(parents=True, exist_ok=True)
    lauf = lambda *args: subprocess.run(
        ["git", *args], cwd=pfad, capture_output=True, check=True
    )
    lauf("init", "-q")
    lauf("config", "user.email", "test@example.invalid")
    lauf("config", "user.name", "Test")
    lauf("config", "commit.gpgsign", "false")
    (pfad / "a.txt").write_text("eins", encoding="utf-8")
    lauf("add", "a.txt")
    lauf("commit", "-q", "-m", "Der erste Schritt", "--no-verify")
    return pfad


def test_a_folder_without_git_reports_no_commits(projekt):
    assert activity.git_commits(projekt) == []
    assert activity.git_pending(projekt) is None


def test_the_last_commits_are_reported(tmp_path):
    repo = git_repo(tmp_path / "repo")
    (zeile,) = activity.git_commits(repo)
    assert "Der erste Schritt" in zeile


def test_a_clean_repository_has_nothing_pending(tmp_path):
    repo = git_repo(tmp_path / "repo")
    assert activity.git_pending(repo) is None


def test_changed_and_new_files_are_counted_apart(tmp_path):
    repo = git_repo(tmp_path / "repo")
    (repo / "a.txt").write_text("zwei", encoding="utf-8")
    (repo / "neu.txt").write_text("x", encoding="utf-8")
    text = activity.git_pending(repo)
    assert "1 geändert" in text
    assert "1 neu" in text


# --- Zuletzt geaenderte Dateien -------------------------------------------


def test_recent_files_come_back_newest_first(projekt):
    for i, name in enumerate(("alt.txt", "neu.txt")):
        datei = projekt / name
        datei.write_text("x", encoding="utf-8")
        alt = time.time() - (100 - i * 50)
        os.utime(datei, (alt, alt))
    assert [e.what for e in activity.recent_files(projekt)] == ["neu.txt", "alt.txt"]


@pytest.mark.parametrize(
    "muell", [".git", "node_modules", "__pycache__", "build", "dist", ".pytest_cache"]
)
def test_noise_folders_are_left_out(projekt, muell):
    """Sonst stuenden in der Notiz nur Build-Erzeugnisse."""
    (projekt / muell).mkdir()
    (projekt / muell / "x.txt").write_text("x", encoding="utf-8")
    (projekt / "echt.txt").write_text("x", encoding="utf-8")
    assert [e.what for e in activity.recent_files(projekt)] == ["echt.txt"]


def test_the_note_itself_is_not_listed(projekt):
    """Sie ist immer die juengste Datei - sie stuende sonst jedes Mal
    ganz oben und verdraengte, worum es geht."""
    from projecthq.scanner import NOTE_NAME

    (projekt / NOTE_NAME).write_text("x", encoding="utf-8")
    (projekt / "echt.txt").write_text("x", encoding="utf-8")
    assert [e.what for e in activity.recent_files(projekt)] == ["echt.txt"]


def test_a_file_in_a_subfolder_keeps_its_path(projekt):
    (projekt / "src").mkdir()
    (projekt / "src" / "main.py").write_text("x", encoding="utf-8")
    (eintrag,) = activity.recent_files(projekt)
    assert eintrag.what.replace("\\", "/") == "src/main.py"


def test_recent_files_stops_at_its_budget(projekt):
    for i in range(30):
        (projekt / f"f{i}.txt").write_text("x", encoding="utf-8")
    assert len(activity.recent_files(projekt, limit=4)) == 4


# --- Der fertige Block ----------------------------------------------------


def test_the_block_carries_a_dated_heading(projekt, archive):
    block = activity.status_block(projekt)
    assert block.startswith("## Stand vom ")


def test_a_source_without_anything_to_say_leaves_no_heading(projekt, archive):
    """Ein leerer Abschnitt waere schlimmer als gar keiner."""
    block = activity.status_block(projekt)
    assert "Woran gearbeitet wurde" not in block
    assert "Letzte Commits" not in block


def test_the_block_names_what_was_worked_on(projekt, archive):
    claude, _codex = archive
    claude_session(
        claude / activity.claude_folder_name(projekt),
        "s1",
        str(projekt),
        titel="Admin-Startoptionen",
    )
    block = activity.status_block(projekt)
    assert "Woran gearbeitet wurde" in block
    assert "Admin-Startoptionen" in block


def test_the_block_reports_commits_and_pending_work(tmp_path):
    repo = git_repo(tmp_path / "repo")
    (repo / "neu.txt").write_text("x", encoding="utf-8")
    block = activity.status_block(repo)
    assert "Der erste Schritt" in block
    assert "Nicht committet" in block


def test_the_block_ends_with_a_blank_line(projekt, archive):
    """Sonst klebte der naechste Block daran, wenn er oben eingefuegt wird."""
    assert activity.status_block(projekt).endswith("\n")


def test_a_long_topic_is_shortened(projekt, archive):
    claude, _codex = archive
    claude_session(
        claude / activity.claude_folder_name(projekt),
        "s1",
        str(projekt),
        prompts=("wort " * 200,),
    )
    zeile = next(
        z for z in activity.status_block(projekt).splitlines() if z.startswith("- ")
    )
    assert len(zeile) < 120


def test_timestamps_are_shown_in_local_time(projekt, archive):
    """Die Archive schreiben UTC. Ungerechnet staende in der Notiz eine
    Uhrzeit, zu der niemand am Rechner sass."""
    claude, _codex = archive
    claude_session(
        claude / activity.claude_folder_name(projekt), "s1", str(projekt), titel="x"
    )
    (eintrag,) = activity.claude_sessions(projekt)
    erwartet = time.strftime("%d.%m. %H:%M", time.localtime(eintrag.when))
    assert erwartet in activity.status_block(projekt)


def test_nothing_at_all_still_gives_a_usable_block(projekt, archive):
    """Ein Projekt, zu dem es nichts zu sagen gibt, bekommt trotzdem eine
    brauchbare Datei - sonst stuende der Nutzer vor einem leeren Blatt."""
    block = activity.status_block(projekt)
    assert "## Stand vom " in block
    assert len(block.strip().splitlines()) >= 2


# --- Die juengste Aenderung im Projekt ------------------------------------


def altern(pfad: Path, sekunden: float) -> None:
    """Setzt die Aenderungszeit zurueck."""
    alt = time.time() - sekunden
    os.utime(pfad, (alt, alt))


def test_a_file_deep_inside_counts_as_a_change(projekt):
    """Der Kern der Sache: die Ordnerzeit aendert sich nicht, wenn in
    einer Datei getippt wird - und schon gar nicht in einem Unterordner.
    Gemessen an 'Webshop': Ordner 02.08., juengste Datei 07.09.
    """
    tief = projekt / "docs" / "notizen"
    tief.mkdir(parents=True)
    datei = tief / "text.md"
    datei.write_text("x", encoding="utf-8")
    altern(projekt, 30 * 86400)

    assert activity.newest_change(projekt) >= datei.stat().st_mtime - 1


def test_an_empty_project_falls_back_to_the_folder_time(projekt):
    """Findet der Durchlauf keine Datei, bleibt nur die Ordnerzeit."""
    ordnerzeit = projekt.stat().st_mtime
    assert activity.newest_change(projekt) == pytest.approx(ordnerzeit, abs=1)


def test_a_truncated_walk_keeps_the_folder_time_as_a_floor(projekt):
    """Wenn das Budget nicht reicht, weiss HQ es nicht besser - dann ist
    die Ordnerzeit die bessere Auskunft als eine zufaellig frueh
    gefundene Datei."""
    for i in range(50):
        datei = projekt / f"f{i}.txt"
        datei.write_text("x", encoding="utf-8")
        alt = time.time() - 400 * 86400
        os.utime(datei, (alt, alt))

    knapp = activity.newest_change(projekt, file_budget=1)
    assert knapp == pytest.approx(projekt.stat().st_mtime, abs=1)


def test_writing_the_note_does_not_make_the_project_look_fresh(projekt):
    """HQ soll die Liste nicht mit den eigenen Schreibvorgaengen umsortieren.

    Das Anlegen der Notiz hebt die Ordnerzeit an - sie ist ein neuer
    Eintrag im Verzeichnis. Waere die Ordnerzeit die Untergrenze, schoebe
    schon ein Blick in die Aufgaben das Projekt nach oben. Gemessen: nach
    dem Anlegen standen 'Archiv', 'Spiel' und 'Werkzeuge' auf
    dem heutigen Datum, ohne dass darin gearbeitet worden waere.
    """
    from projecthq.scanner import NOTE_NAME

    echt = projekt / "code.py"
    echt.write_text("x", encoding="utf-8")
    altern(echt, 10 * 86400)
    altern(projekt, 10 * 86400)
    vorher = activity.newest_change(projekt)

    (projekt / NOTE_NAME).write_text("# Aufgaben", encoding="utf-8")
    assert activity.newest_change(projekt) == pytest.approx(vorher, abs=1)


def test_a_vanished_folder_reports_nothing(tmp_path):
    assert activity.newest_change(tmp_path / "gibtsnicht") == 0.0


def test_noise_folders_do_not_count_as_a_change(projekt):
    """Ein Build darf das Projekt nicht frisch aussehen lassen.

    Gealtert wird erst danach: das Anlegen des Unterordners hebt die
    Ordnerzeit selbst an, und die ist der Boden des Ergebnisses.
    """
    (projekt / "node_modules").mkdir()
    frisch = projekt / "node_modules" / "x.js"
    frisch.write_text("x", encoding="utf-8")
    altern(projekt, 30 * 86400)
    assert activity.newest_change(projekt) < frisch.stat().st_mtime - 60


def test_the_note_does_not_count_as_a_change(projekt):
    """Sonst schoebe jedes 'Stand einfuegen' das Projekt nach oben - und
    die Liste zeigte, woran HQ gearbeitet hat, nicht der Nutzer."""
    from projecthq.scanner import NOTE_NAME

    echt = projekt / "code.py"
    echt.write_text("x", encoding="utf-8")
    notiz = projekt / NOTE_NAME
    notiz.write_text("x", encoding="utf-8")
    altern(echt, 30 * 86400)
    altern(projekt, 30 * 86400)

    assert activity.newest_change(projekt) < notiz.stat().st_mtime - 60


# --- Womit zuletzt gearbeitet wurde ---------------------------------------


def test_the_index_names_the_agent_of_each_project(projekt, archive):
    claude, codex = archive
    anderes = projekt.parent / "Anderes"
    anderes.mkdir()
    claude_session(
        claude / activity.claude_folder_name(projekt), "c", str(projekt), titel="x"
    )
    codex_session(codex / "2026", "x", str(anderes), prompts=("y",))

    index = activity.agent_index([projekt, anderes])
    assert index[str(projekt).casefold()][0] == "claude"
    assert index[str(anderes).casefold()][0] == "codex"


def test_the_newer_agent_wins(projekt, archive):
    """Wer zuletzt da war, steht in der Spalte."""
    claude, codex = archive
    claude_session(
        claude / activity.claude_folder_name(projekt),
        "c",
        str(projekt),
        titel="alt",
        alter=7200,
    )
    codex_session(codex / "2026", "x", str(projekt), prompts=("neu",), alter=60)
    index = activity.agent_index([projekt])
    assert index[str(projekt).casefold()][0] == "codex"


def test_a_project_without_sessions_is_not_in_the_index(projekt, archive):
    assert activity.agent_index([projekt]) == {}


def test_the_index_reads_the_codex_archive_only_once(projekt, archive, monkeypatch):
    """Der Grund fuer den Index: einzeln kostete es 2,6 s fuer 24
    Projekte, in einem Durchgang 33 ms."""
    _claude, codex = archive
    for i in range(3):
        codex_session(codex / "2026", f"s{i}", str(projekt), prompts=("x",))

    gelesen = []
    echtes_open = Path.open

    def zaehlend(self, *a, **k):
        if self.suffix == ".jsonl":
            gelesen.append(self)
        return echtes_open(self, *a, **k)

    monkeypatch.setattr(Path, "open", zaehlend)
    viele = [projekt.parent / f"P{i}" for i in range(10)]
    for p in viele:
        p.mkdir(exist_ok=True)
    activity.agent_index([projekt, *viele])

    # Drei Codex-Dateien, jede genau einmal fuer den Kopfsatz geoeffnet.
    assert len([g for g in gelesen if "rollout" in g.name]) == 3


# --- Der Zwischenspeicher -------------------------------------------------


def test_the_snapshot_computes_once_and_then_remembers(projekt, archive):
    schnapp = activity.Snapshot()
    erst = schnapp.changed(projekt)

    (projekt / "neu.txt").write_text("x", encoding="utf-8")
    assert schnapp.changed(projekt) == erst, "gemerkter Wert soll gelten"


def test_clearing_the_snapshot_makes_it_look_again(projekt, archive):
    schnapp = activity.Snapshot()
    erst = schnapp.changed(projekt)

    zukunft = time.time() + 600
    datei = projekt / "neu.txt"
    datei.write_text("x", encoding="utf-8")
    os.utime(datei, (zukunft, zukunft))

    schnapp.clear()
    assert schnapp.changed(projekt) > erst


def test_a_project_the_snapshot_never_saw_is_computed(projekt, archive):
    """Ein Ordner, der nebenher im Explorer entsteht, soll sein richtiges
    Datum bekommen - ohne dass jemand Strg+R druecken muss."""
    schnapp = activity.Snapshot()
    schnapp.changed(projekt)

    frisch = projekt.parent / "Frisch"
    frisch.mkdir()
    assert schnapp.changed(frisch) > 0


def test_the_snapshot_reports_the_agent(projekt, archive):
    claude, _codex = archive
    claude_session(
        claude / activity.claude_folder_name(projekt), "c", str(projekt), titel="x"
    )
    schnapp = activity.Snapshot()
    assert schnapp.agent(projekt, [projekt]) == "claude"


def test_the_snapshot_reports_no_agent_when_there_is_none(projekt, archive):
    schnapp = activity.Snapshot()
    assert schnapp.agent(projekt, [projekt]) == ""


def test_forgetting_only_the_agents_keeps_the_dates(projekt, archive):
    """Nach einem Start ueber HQ soll das Archiv neu befragt werden - aber
    die teure Suche nach der juengsten Datei nicht noch einmal laufen."""
    schnapp = activity.Snapshot()
    datum = schnapp.changed(projekt)
    schnapp.agent(projekt, [projekt])

    schnapp.forget_agents()

    laeufe = []
    echt = activity.newest_change
    activity.newest_change = lambda p, **k: (laeufe.append(p), echt(p, **k))[1]
    try:
        assert schnapp.changed(projekt) == datum
        assert laeufe == [], "das Datum war gemerkt und bleibt es"
    finally:
        activity.newest_change = echt
