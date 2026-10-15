import dataclasses
import json
import os
import time
from pathlib import Path

from projecthq.scanner import (
    DEFAULT_SORT_DESC,
    DEFAULT_SORT_KEY,
    NOTE_NAME,
    SORT_KEYS,
    Project,
    detect_kind,
    scan,
    sort_projects,
)


def make(tmp_path: Path, name: str, files: dict[str, str] | None = None) -> Path:
    root = tmp_path / name
    root.mkdir(parents=True, exist_ok=True)
    for rel, content in (files or {}).items():
        target = root / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
    return root


def test_detect_start_bat(tmp_path):
    p = make(tmp_path, "A", {"start_rechner.bat": "echo hi"})
    assert detect_kind(p) == "bat"


def test_detect_german_starten_cmd(tmp_path):
    p = make(tmp_path, "A", {"Claude starten.cmd": "echo hi"})
    assert detect_kind(p) == "bat"


def test_detect_node_project(tmp_path):
    p = make(
        tmp_path,
        "A",
        {"package.json": json.dumps({"scripts": {"dev": "next dev"}})},
    )
    assert detect_kind(p) == "node"


def test_detect_node_without_scripts(tmp_path):
    p = make(tmp_path, "A", {"package.json": json.dumps({"name": "x"})})
    assert detect_kind(p) == "node"


def test_detect_node_with_corrupt_package_json(tmp_path):
    p = make(tmp_path, "A", {"package.json": "{ broken"})
    assert detect_kind(p) == "node"


def test_detect_python_main(tmp_path):
    p = make(tmp_path, "A", {"main.py": "print(1)"})
    assert detect_kind(p) == "py"


def test_detect_python_app(tmp_path):
    p = make(tmp_path, "A", {"app.py": "print(1)"})
    assert detect_kind(p) == "py"


def test_detect_dotnet_solution(tmp_path):
    p = make(tmp_path, "A", {"App.sln": ""})
    assert detect_kind(p) == "dotnet"


def test_detect_bat_wins_over_package_json(tmp_path):
    p = make(
        tmp_path,
        "A",
        {"start.bat": "echo", "package.json": json.dumps({"scripts": {"dev": "x"}})},
    )
    assert detect_kind(p) == "bat"


def test_detect_docker_compose(tmp_path):
    p = make(tmp_path, "A", {"docker-compose.yml": "services: {}"})
    assert detect_kind(p) == "docker"


def test_detect_compose_short_filename(tmp_path):
    p = make(tmp_path, "A", {"compose.yml": "services: {}"})
    assert detect_kind(p) == "docker"


def test_detect_static_website(tmp_path):
    p = make(tmp_path, "A", {"index.html": "<h1>hi</h1>", "styles.css": ""})
    assert detect_kind(p) == "web"


def test_detect_website_wins_over_readme(tmp_path):
    p = make(tmp_path, "A", {"index.html": "<h1>hi</h1>", "README.md": "# doku"})
    assert detect_kind(p) == "web"


def test_detect_python_wins_over_docker_compose(tmp_path):
    p = make(tmp_path, "A", {"main.py": "", "docker-compose.yml": ""})
    assert detect_kind(p) == "py"


def test_detect_docs_only(tmp_path):
    p = make(tmp_path, "A", {"README.md": "# hi"})
    assert detect_kind(p) == "docs"


def test_detect_empty_folder(tmp_path):
    p = make(tmp_path, "A")
    assert detect_kind(p) == "-"


def test_scan_lists_directories_only(tmp_path):
    make(tmp_path, "Alpha", {"main.py": ""})
    make(tmp_path, "Beta", {"README.md": ""})
    (tmp_path / "lose_datei.zip").write_text("x", encoding="utf-8")
    names = {p.name for p in scan(tmp_path)}
    assert names == {"Alpha", "Beta"}


def test_scan_skips_dot_directories(tmp_path):
    make(tmp_path, "Alpha")
    make(tmp_path, ".git")
    assert [p.name for p in scan(tmp_path)] == ["Alpha"]


def test_scan_missing_root_returns_empty(tmp_path):
    assert scan(tmp_path / "gibtsnicht") == []


def test_scan_leaves_the_order_to_sort_projects(tmp_path):
    """scan liefert, was im Ordner liegt - in welcher Reihenfolge es in der
    Liste steht, entscheidet allein `sort_projects`.

    Frueher sortierte scan zusaetzlich nach mtime, und `window.refresh`
    sortierte das Ergebnis unmittelbar danach neu: die erste Sortierung war
    ohne jede Wirkung.
    """
    a = make(tmp_path, "Alt", {"main.py": ""})
    b = make(tmp_path, "Neu", {"main.py": ""})
    os.utime(a, (time.time() - 10_000, time.time() - 10_000))
    os.utime(b, (time.time(), time.time()))
    assert [p.name for p in scan(tmp_path)] == ["Alt", "Neu"]


# --- Zeitstempel und vereinfachte Erkennung -------------------------------


def test_scan_reports_creation_and_modification_time(tmp_path):
    make(tmp_path, "Alpha")
    project = scan(tmp_path)[0]
    assert project.created > 0
    assert project.mtime > 0


def test_created_stays_when_content_changes(tmp_path):
    root = make(tmp_path, "Alpha")
    before = scan(tmp_path)[0].created
    time.sleep(0.05)
    (root / "neu.txt").write_text("x", encoding="utf-8")
    os.utime(root, None)
    after = scan(tmp_path)[0]
    assert after.created == before
    assert after.mtime >= before


def test_detect_kind_returns_the_type_only(tmp_path):
    root = make(tmp_path, "Alpha", {"start.bat": "echo x"})
    assert detect_kind(root) == "bat"


# --- Sortierung -----------------------------------------------------------


def projects_for_sorting(tmp_path: Path):
    """Drei Projekte mit bekannten Namen, Typen und Zeitstempeln."""
    now = time.time()
    make(tmp_path, "beta", {"main.py": ""})          # py
    make(tmp_path, "Alpha", {"package.json": "{}"})  # node
    make(tmp_path, "Gamma", {"README.md": "# x"})    # docs
    os.utime(tmp_path / "beta", (now - 300, now - 300))
    os.utime(tmp_path / "Alpha", (now - 200, now - 200))
    os.utime(tmp_path / "Gamma", (now - 100, now - 100))
    return scan(tmp_path)


def names(projects) -> list[str]:
    return [p.name for p in projects]


def test_sort_by_name_ignores_upper_and_lower_case(tmp_path):
    projects = projects_for_sorting(tmp_path)
    assert names(sort_projects(projects, "name", desc=False)) == [
        "Alpha",
        "beta",
        "Gamma",
    ]


def test_sort_by_name_descending(tmp_path):
    projects = projects_for_sorting(tmp_path)
    assert names(sort_projects(projects, "name", desc=True)) == [
        "Gamma",
        "beta",
        "Alpha",
    ]


def test_sort_by_modification_time(tmp_path):
    projects = projects_for_sorting(tmp_path)
    assert names(sort_projects(projects, "mtime", desc=True)) == [
        "Gamma",
        "Alpha",
        "beta",
    ]
    assert names(sort_projects(projects, "mtime", desc=False)) == [
        "beta",
        "Alpha",
        "Gamma",
    ]


def test_sort_by_creation_time(tmp_path):
    projects = projects_for_sorting(tmp_path)
    ordered = sort_projects(projects, "created", desc=False)
    stamps = [p.created for p in ordered]
    assert stamps == sorted(stamps)


def test_sort_by_kind_falls_back_to_the_name(tmp_path):
    projects = projects_for_sorting(tmp_path)
    make(tmp_path, "aaa", {"README.md": "# x"})  # zweites docs-Projekt
    projects = scan(tmp_path)
    ordered = names(sort_projects(projects, "kind", desc=False))
    # docs < node < py, und innerhalb von docs alphabetisch
    assert ordered == ["aaa", "Gamma", "Alpha", "beta"]


def test_sort_keeps_names_ascending_within_a_group_when_descending(tmp_path):
    projects_for_sorting(tmp_path)
    make(tmp_path, "aaa", {"README.md": "# x"})
    ordered = names(sort_projects(scan(tmp_path), "kind", desc=True))
    assert ordered == ["beta", "Alpha", "aaa", "Gamma"]


def test_sort_with_unknown_key_uses_the_default(tmp_path):
    projects = projects_for_sorting(tmp_path)
    assert names(sort_projects(projects, "gibtsnicht", desc=False)) == names(
        sort_projects(projects, DEFAULT_SORT_KEY, DEFAULT_SORT_DESC)
    )


def test_sort_does_not_touch_the_original_list(tmp_path):
    projects = projects_for_sorting(tmp_path)
    before = names(projects)
    sort_projects(projects, "name", desc=False)
    assert names(projects) == before


def test_every_sort_key_is_a_field_of_a_project():
    """`sort_projects` liest die Schluessel mit `getattr` vom Projekt.

    Ein Schluessel ohne Feld faellt deshalb erst beim Klick auf die Spalte
    auf - und dann mit einem AttributeError mitten in der Oberflaeche.
    """
    fields = {f.name for f in dataclasses.fields(Project)}
    assert set(SORT_KEYS) <= fields


# --- Favoriten stehen oben ------------------------------------------------


def test_favorites_come_first(tmp_path):
    projects = projects_for_sorting(tmp_path)
    ordered = names(sort_projects(projects, "name", desc=False, favorites=["Gamma"]))
    assert ordered == ["Gamma", "Alpha", "beta"]


def test_favorites_keep_the_chosen_order_among_themselves(tmp_path):
    projects = projects_for_sorting(tmp_path)
    ordered = names(
        sort_projects(projects, "name", desc=False, favorites=["Gamma", "beta"])
    )
    assert ordered == ["beta", "Gamma", "Alpha"]


def test_favorites_stay_on_top_in_every_direction(tmp_path):
    projects = projects_for_sorting(tmp_path)
    for desc in (True, False):
        ordered = names(sort_projects(projects, "mtime", desc=desc, favorites=["beta"]))
        assert ordered[0] == "beta"


def test_a_favorite_without_a_folder_changes_nothing(tmp_path):
    """Ein Eintrag aus der config.json, dessen Ordner nicht mehr da ist."""
    projects = projects_for_sorting(tmp_path)
    plain = names(sort_projects(projects, "name", desc=False))
    assert names(sort_projects(projects, "name", desc=False, favorites=["Weg"])) == plain


def test_sorting_without_favorites_is_unchanged(tmp_path):
    projects = projects_for_sorting(tmp_path)
    assert names(sort_projects(projects, "name", desc=False, favorites=[])) == [
        "Alpha",
        "beta",
        "Gamma",
    ]


# --- Notiz und Agent ------------------------------------------------------


def test_a_project_without_a_note_says_so(tmp_path):
    make(tmp_path, "Alpha")
    (alpha,) = scan(tmp_path)
    assert alpha.has_note is False


def test_a_project_with_a_note_is_recognised(tmp_path):
    make(tmp_path, "Alpha", {NOTE_NAME: "# Aufgaben"})
    (alpha,) = scan(tmp_path)
    assert alpha.has_note is True


def test_an_empty_note_still_counts(tmp_path):
    """Angelegt ist angelegt - sonst verschwaende das Symbol wieder,
    sobald jemand den Inhalt loescht, aber die Datei behaelt."""
    make(tmp_path, "Alpha", {NOTE_NAME: ""})
    (alpha,) = scan(tmp_path)
    assert alpha.has_note is True


def test_a_folder_named_like_the_note_is_not_a_note(tmp_path):
    root = make(tmp_path, "Alpha")
    (root / NOTE_NAME).mkdir()
    (alpha,) = scan(tmp_path)
    assert alpha.has_note is False


def test_the_scanner_leaves_the_agent_empty(tmp_path):
    """Womit ein Projekt zuletzt lief, steht in der Konfiguration - im
    Ordner ist davon nichts zu sehen. Das Fenster traegt es nach."""
    make(tmp_path, "Alpha")
    (alpha,) = scan(tmp_path)
    assert alpha.agent == ""


def test_both_new_columns_can_be_sorted_by(tmp_path):
    assert "agent" in SORT_KEYS
    assert "has_note" in SORT_KEYS


def _project(name: str, **kwargs) -> Project:
    base = dict(path=Path(name), kind="-", created=0.0, mtime=0.0)
    return Project(name=name, **{**base, **kwargs})


def test_sorting_by_agent_groups_the_same_agent_together(tmp_path):
    projects = [
        _project("A", agent="codex"),
        _project("B", agent=""),
        _project("C", agent="claude"),
        _project("D", agent="codex"),
    ]
    order = [p.name for p in sort_projects(projects, "agent", desc=True)]
    assert order == ["A", "D", "C", "B"]


def test_sorting_by_note_puts_projects_with_a_note_first(tmp_path):
    projects = [
        _project("A", has_note=False),
        _project("B", has_note=True),
        _project("C", has_note=False),
    ]
    order = [p.name for p in sort_projects(projects, "has_note", desc=True)]
    assert order[0] == "B"


def test_projects_without_an_agent_still_sort_by_name(tmp_path):
    """Innerhalb einer Gruppe gilt der Name, aufsteigend - wie bei jeder
    anderen Spalte auch."""
    projects = [_project("Zeta"), _project("Alpha"), _project("Mitte")]
    order = [p.name for p in sort_projects(projects, "agent", desc=True)]
    assert order == ["Alpha", "Mitte", "Zeta"]
