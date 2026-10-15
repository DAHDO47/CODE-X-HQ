"""Findet Projektordner und bestimmt ihren Typ.

Bewusst ohne Qt-Importe. Einen Startbefehl leitet dieses Modul nicht mehr
ab: jedes Projekt wird gleich gestartet (siehe `runner.claude_command`).
Der Typ dient nur noch der Anzeige.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

START_PATTERNS = ("start*.bat", "start*.cmd", "*starten*.cmd", "*starten*.bat")
COMPOSE_NAMES = ("docker-compose.yml", "docker-compose.yaml", "compose.yml")

#: Die Notizdatei eines Projekts: was als naechstes zu tun ist, und was
#: zuletzt geaendert wurde. Sie liegt im Projektordner selbst und nicht
#: neben der Konfiguration - so wandert sie beim Verschieben mit, ist im
#: Explorer zu finden und kann ins Git. Der Name steht hier, weil dieses
#: Modul als einziges den Ordner liest; `runner` legt sie darueber an.
NOTE_NAME = "AUFGABEN.md"


def _first_match(path: Path, patterns: tuple[str, ...]) -> Path | None:
    for pattern in patterns:
        try:
            matches = sorted(path.glob(pattern))
        except OSError:
            continue
        if matches:
            return matches[0]
    return None


def detect_kind(path: Path) -> str:
    """Liefert den Typ eines Projektordners. Der erste Treffer gewinnt."""
    if _first_match(path, START_PATTERNS) is not None:
        return "bat"

    if (path / "package.json").exists():
        return "node"

    for entry_name in ("main.py", "app.py"):
        if (path / entry_name).exists():
            return "py"

    for compose_name in COMPOSE_NAMES:
        if (path / compose_name).exists():
            return "docker"

    if _first_match(path, ("*.sln", "*.csproj")) is not None:
        return "dotnet"

    # Statische Website. Muss vor der Doku-Pruefung stehen, sonst gewinnt
    # ein danebenliegendes README.
    if (path / "index.html").exists():
        return "web"

    if _first_match(path, ("*.md", "docs")) is not None:
        return "docs"

    return "-"


@dataclass
class Project:
    name: str
    path: Path
    kind: str
    created: float
    mtime: float
    #: Ob im Ordner eine Notiz liegt. Was darin steht, liest der Launcher
    #: nicht - die Spalte zeigt nur, dass es etwas zu lesen gibt.
    has_note: bool = False
    #: Womit das Projekt zuletzt gestartet wurde. Der Scanner laesst das
    #: Feld leer: im Ordner steht es nicht, es kommt aus der Konfiguration
    #: und wird vom Fenster nachgetragen (siehe `MainWindow.refresh`). Das
    #: Feld sitzt trotzdem hier, damit `sort_projects` danach sortieren
    #: kann wie nach jeder anderen Spalte.
    agent: str = ""


def _timestamps(entry: Path) -> tuple[float, float]:
    """(erstellt, zuletzt geaendert). Bei Fehlern beides 0."""
    try:
        stat = entry.stat()
    except OSError:
        return 0.0, 0.0
    # st_birthtime gibt es unter Windows erst ab Python 3.12; davor und auf
    # anderen Systemen ist st_ctime der naechstbeste Wert.
    created = getattr(stat, "st_birthtime", None) or stat.st_ctime
    return float(created), float(stat.st_mtime)


def scan(root: Path) -> list[Project]:
    root = Path(root)
    if not root.is_dir():
        return []

    projects: list[Project] = []
    for entry in sorted(root.iterdir()):
        if not entry.is_dir() or entry.name.startswith("."):
            continue
        created, mtime = _timestamps(entry)
        projects.append(
            Project(
                name=entry.name,
                path=entry,
                kind=detect_kind(entry),
                created=created,
                mtime=mtime,
                has_note=(entry / NOTE_NAME).is_file(),
            )
        )

    # Keine Sortierung: die ist Sache von `sort_projects`, und die
    # Oberflaeche ruft es unmittelbar nach jedem Scan auf.
    return projects


# --- Sortierung -----------------------------------------------------------

# Die Schluessel sind Feldnamen von `Project`; die Oberflaeche reicht sie
# durch, ohne sie zu uebersetzen.
SORT_KEYS = ("name", "kind", "agent", "has_note", "created", "mtime")
DEFAULT_SORT_KEY = "mtime"
DEFAULT_SORT_DESC = True

# Erster Klick auf eine Spalte: Datumsspalten beginnen mit dem juengsten
# Eintrag, Text beginnt bei A. Agent und Notiz beginnen ebenfalls
# absteigend, denn aufsteigend stuenden zuerst die Projekte ohne Eintrag -
# also gerade die, nach denen niemand sucht, wenn er die Spalte anklickt.
SORT_STARTS_DESCENDING = {
    "created": True,
    "mtime": True,
    "agent": True,
    "has_note": True,
}


def sort_projects(
    projects: list[Project],
    key: str = DEFAULT_SORT_KEY,
    desc: bool = DEFAULT_SORT_DESC,
    favorites: Iterable[str] = (),
) -> list[Project]:
    """Sortierte Kopie. Ein unbekannter Schluessel faellt auf die Vorgabe zurueck.

    Gleiche Werte werden nach Namen aufgeloest, und zwar immer aufsteigend:
    innerhalb einer Typgruppe soll die Reihenfolge nicht davon abhaengen, in
    welche Richtung die Gruppen selbst stehen.

    `favorites` hebt Projekte an den Anfang, ohne ihre Reihenfolge
    untereinander anzutasten: oben wie unten gilt dieselbe Sortierung.
    Namen ohne Ordner stoeren dabei nicht - sie kommen schlicht nicht vor.
    """
    if key not in SORT_KEYS:
        key, desc = DEFAULT_SORT_KEY, DEFAULT_SORT_DESC

    by_name = sorted(
        projects, key=lambda p: p.name.casefold(), reverse=(key == "name" and desc)
    )
    ordered = (
        by_name
        if key == "name"
        else sorted(by_name, key=lambda p: getattr(p, key), reverse=desc)
    )

    pinned = set(favorites)
    if not pinned:
        return ordered
    # Stabil: die Sortierung von eben bleibt innerhalb beider Gruppen.
    return sorted(ordered, key=lambda p: p.name not in pinned)
