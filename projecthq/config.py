"""Persistente Einstellungen des Launchers.

Bewusst ohne Qt-Importe, damit die Logik ohne laufende GUI testbar ist.
"""

from __future__ import annotations

import json
import os
import sys
from dataclasses import dataclass, field
from pathlib import Path

from .i18n import DEFAULT_LANGUAGE, resolve_language
from .scanner import DEFAULT_SORT_DESC, DEFAULT_SORT_KEY, SORT_KEYS
from .theme import DEFAULT_THEME, THEMES

DEFAULT_ROOT = Path.home() / "Projekte"

APP_NAME = "ProjectHQ"

#: Wie die Konsole aussieht, in der ein Projekt startet. 'crt' faerbt sie
#: im Look des Launchers, 'classic' laesst sie so, wie Windows sie oeffnet.
#: Die Konstanten stehen hier und nicht in `runner`, weil `runner` bereits
#: die Konfiguration importiert - andersherum entstuende ein Ringschluss.
CONSOLE_STYLES = ("crt", "classic")
DEFAULT_CONSOLE_STYLE = "crt"

#: Womit ein Projekt startet. Der Name ist zugleich der Befehl, der in der
#: Konsole laeuft. Aus demselben Grund wie die Konsolen-Designs stehen sie
#: hier und nicht in `runner`: der importiert bereits die Konfiguration.
AGENTS = ("claude", "codex")
DEFAULT_AGENT = "claude"

#: Wie ein Agent heisst und was er ist. Beides steht hier und nicht in der
#: Oberflaeche, damit ein dritter Agent an genau einer Stelle entsteht:
#: Name oben eintragen, Beschriftung und Zusatz hier dazu.
AGENT_LABELS = {
    "claude": "CLAUDE",
    "codex": "CODEX",
}
AGENT_NOTES = {
    "claude": "Claude Code",
    "codex": "OpenAI Codex CLI",
}

#: Das Zeichen, das den Agenten in der Liste vertritt. Es muss in der
#: Listenschrift genau so breit sein wie eine Ziffer, sonst verschiebt es
#: alle Spalten dahinter - gemessen: Consolas hat weder das eine noch das
#: andere Zeichen selbst, aber die einspringende Ersatzschrift malt Kreis
#: und Quadrat auf voller Zeichenbreite, eine Raute dagegen breiter.
#: `tests/test_window.py` misst nach.
#: Die Shell, in der der Agent laeuft. Fuer den Agenten selbst macht das
#: kaum einen Unterschied - seine eigenen Werkzeuge waehlt er selbst -,
#: aber PowerShell laedt das eigene Profil, `cmd` nicht.
SHELLS = ("cmd", "powershell")
DEFAULT_SHELL = "cmd"
SHELL_LABELS = {
    "cmd": "CMD",
    "powershell": "POWERSHELL",
}


def resolve_shell(shell: object) -> str:
    """Wie `resolve_agent`: Unbekanntes wird zur Vorgabe, statt zu kippen."""
    return shell if shell in SHELLS else DEFAULT_SHELL


AGENT_MARKS = {
    "claude": "■",  # gefuelltes Quadrat
    "codex": "●",  # gefuellter Kreis
}


def resolve_agent(agent: object) -> str:
    """Der Agent, der wirklich laufen wird.

    Ein unbekannter Name - von Hand in die `config.json` geschrieben, aus
    einer aelteren Version uebrig - verweigert nicht den Start, sondern
    wird zur Vorgabe. Wer melden will, was tatsaechlich fehlt, fragt hier
    und liest den Namen nicht aus einem fertigen Befehl zurueck.
    """
    return agent if agent in AGENTS else DEFAULT_AGENT


# --- Wo die Datei liegt ---------------------------------------------------


def config_location() -> Path:
    """Die Einstellungen liegen im Benutzerprofil, nicht neben der .exe.

    Neben der .exe waeren sie nach jedem Build verschwunden: `build.ps1`
    laesst PyInstaller mit `--noconfirm` laufen, und das raeumt
    `dist\\ProjectHQ` vorher leer. Ohne `APPDATA` - das gibt es unter
    Windows immer, aber nicht ueberall sonst - tut es das Benutzerprofil.
    """
    base = os.environ.get("APPDATA")
    if base:
        return Path(base) / APP_NAME / "config.json"
    return Path.home() / f".{APP_NAME.lower()}" / "config.json"


def legacy_location() -> Path:
    """Wo die Datei bis zur Umstellung lag: neben der .exe, sonst neben main.py."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent / "config.json"
    return Path(__file__).resolve().parent.parent / "config.json"


def adopt_legacy(target: Path, legacy: Path) -> bool:
    """Holt die Einstellungen einmalig vom alten Ort an den neuen.

    Kopiert statt verschoben: eine aeltere .exe daneben findet ihre Datei
    danach weiterhin vor. Liegt am neuen Ort schon etwas, gilt das - der
    alte Stand ist dann der aeltere. Meldet, ob etwas uebernommen wurde.
    """
    target, legacy = Path(target), Path(legacy)
    if target.exists() or not legacy.is_file():
        return False
    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(legacy.read_bytes())
    except OSError:
        return False
    return True


@dataclass
class Config:
    projects_root: Path = DEFAULT_ROOT
    favorites: list[str] = field(default_factory=list)
    sort_key: str = DEFAULT_SORT_KEY
    sort_desc: bool = DEFAULT_SORT_DESC
    console_style: str = DEFAULT_CONSOLE_STYLE
    #: Das Design der Oberflaeche selbst - anders als `console_style`, das
    #: nur die Konsole faerbt, in der ein Projekt startet.
    app_theme: str = DEFAULT_THEME
    #: Die Sprache der Oberflaeche, siehe `i18n`.
    language: str = DEFAULT_LANGUAGE
    last_agent: str = DEFAULT_AGENT
    #: Die zuletzt im Startdialog gewaehlte Shell. Anders als Admin und
    #: 'ohne Rueckfragen' harmlos genug, um sie zu merken.
    last_shell: str = DEFAULT_SHELL
    #: Projektname -> Agent, mit dem dieses Projekt zuletzt lief. Steht
    #: hier und nicht am `Project`: der Scanner liest den Ordner, und im
    #: Ordner ist nicht zu sehen, womit er zuletzt geoeffnet wurde.
    project_agents: dict[str, str] = field(default_factory=dict)
    #: Projektname -> wann es zuletzt ueber HQ gestartet wurde. Zaehlt fuer
    #: BEARBEITET dazu: die Ordnerzeit merkt nichts von einer Sitzung, in
    #: der keine Datei angefasst wurde - ein Start soll trotzdem als
    #: Aktivitaet gelten.
    project_started: dict[str, float] = field(default_factory=dict)
    #: Wann der geplante Shutdown faellig ist, als Unix-Zeit - 0.0 heisst
    #: 'kein Shutdown geplant'. Der Countdown selbst laeuft in Windows
    #: (`shutdown /t`), nicht in HQ: dieser Wert merkt sich nur, dass und
    #: bis wann einer laeuft, damit ein neu gestartetes HQ ihn wieder
    #: anzeigen kann.
    shutdown_at: float = 0.0

    @classmethod
    def load(cls, path: Path) -> "Config":
        try:
            data = json.loads(Path(path).read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return cls()
        if not isinstance(data, dict):
            return cls()

        # Ein 'commands'-Block aus einer frueheren Version wird stillschweigend
        # uebergangen: eigene Startbefehle gibt es nicht mehr.
        root = data.get("projects_root")
        raw_favorites = data.get("favorites")

        # Sortierung: nur bekannte Schluessel und ein echtes bool werden
        # uebernommen. Eine von Hand verstellte Datei soll den Start nicht
        # kippen, sondern still bei der Vorgabe landen. Taugt die Spalte
        # nicht, ist auch ihre Richtung wertlos - dann faellt beides zurueck.
        sort_key = data.get("sort_key")
        sort_desc = data.get("sort_desc")
        if sort_key not in SORT_KEYS:
            sort_key, sort_desc = DEFAULT_SORT_KEY, DEFAULT_SORT_DESC

        # Dieselbe Regel wie bei der Sortierung: ein unbekanntes Design
        # faellt still auf die Vorgabe zurueck, statt den Start zu kippen.
        console_style = data.get("console_style")
        if console_style not in CONSOLE_STYLES:
            console_style = DEFAULT_CONSOLE_STYLE

        # Dieselbe Regel noch einmal fuer das Design der Oberflaeche.
        app_theme = data.get("app_theme")
        if app_theme not in THEMES:
            app_theme = DEFAULT_THEME

        # Und fuer die Sprache.
        language = resolve_language(data.get("language"))

        # Dieselbe Regel noch einmal fuer die zuletzt getroffene Wahl im
        # Startdialog. Eine Datei aus einer Vorversion kennt sie nicht.
        last_agent = data.get("last_agent")
        if last_agent not in AGENTS:
            last_agent = DEFAULT_AGENT

        # Und fuer die Shell: eine Datei aus einer Vorversion kennt sie nicht.
        last_shell = resolve_shell(data.get("last_shell"))

        # Und dieselbe Regel je Eintrag: ein Projekt mit unbrauchbarem
        # Agenten verliert seinen Eintrag, nicht die ganze Tabelle. In der
        # Liste steht dann ein '-', als waere es nie ueber HQ gestartet.
        raw_agents = data.get("project_agents")
        project_agents = (
            {
                str(name): agent
                for name, agent in raw_agents.items()
                if agent in AGENTS
            }
            if isinstance(raw_agents, dict)
            else {}
        )

        # Dieselbe Regel: ein Eintrag mit unbrauchbarer Zeit verliert nur
        # sich selbst, nicht die ganze Tabelle.
        raw_started = data.get("project_started")
        project_started = (
            {
                str(name): float(when)
                for name, when in raw_started.items()
                if isinstance(when, (int, float)) and not isinstance(when, bool)
            }
            if isinstance(raw_started, dict)
            else {}
        )

        # Dieselbe Regel wie beim Konsolen-Design: eine von Hand verstellte
        # oder veraltete Datei soll den Start nicht kippen, sondern still
        # bei 'kein Shutdown geplant' landen.
        raw_shutdown_at = data.get("shutdown_at")
        shutdown_at = (
            float(raw_shutdown_at)
            if isinstance(raw_shutdown_at, (int, float))
            and not isinstance(raw_shutdown_at, bool)
            else 0.0
        )

        return cls(
            projects_root=Path(root) if isinstance(root, str) and root else DEFAULT_ROOT,
            favorites=[str(x) for x in raw_favorites]
            if isinstance(raw_favorites, list)
            else [],
            sort_key=sort_key,
            sort_desc=sort_desc if isinstance(sort_desc, bool) else DEFAULT_SORT_DESC,
            console_style=console_style,
            app_theme=app_theme,
            language=language,
            last_agent=last_agent,
            last_shell=last_shell,
            project_agents=project_agents,
            project_started=project_started,
            shutdown_at=shutdown_at,
        )

    def save(self, path: Path) -> None:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "projects_root": str(self.projects_root),
            "favorites": self.favorites,
            "sort_key": self.sort_key,
            "sort_desc": self.sort_desc,
            "console_style": self.console_style,
            "app_theme": self.app_theme,
            "language": self.language,
            "last_agent": self.last_agent,
            "last_shell": self.last_shell,
            "project_agents": self.project_agents,
            "project_started": self.project_started,
            "shutdown_at": self.shutdown_at,
        }
        # Erst daneben schreiben, dann umlegen. Bricht das Schreiben
        # mittendrin ab, steht die vorige Datei unversehrt weiter da; sonst
        # bliebe eine halbe zurueck, und `load` faellt daraufhin still auf
        # die Vorgaben zurueck - alle Einstellungen waeren weg.
        temp = path.with_name(path.name + ".neu")
        try:
            temp.write_text(
                json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8"
            )
            os.replace(temp, path)
        except OSError:
            temp.unlink(missing_ok=True)
            raise

    def rename_entry(self, old: str, new: str) -> None:
        """Traegt alles, was unter `old` gemerkt ist, auf `new` um.

        Alles, was einen Projektnamen als Schluessel hat, gehoert hier
        hinein - sonst zeigt eine Einstellung nach dem Umbenennen auf
        einen Ordner, den es nicht mehr gibt.
        """
        if old in self.favorites:
            self.favorites = [new if x == old else x for x in self.favorites]
        if old in self.project_agents:
            self.project_agents[new] = self.project_agents.pop(old)
        if old in self.project_started:
            self.project_started[new] = self.project_started.pop(old)

    def forget(self, name: str) -> None:
        """Loescht alles, was zu einem Projekt gemerkt war.

        Gegenstueck zu `rename_entry`: was der Ordner nicht ueberlebt hat,
        soll auch in der `config.json` nicht stehen bleiben. Ein nie
        gesehener Name ist dabei kein Fehler.
        """
        if name in self.favorites:
            self.favorites.remove(name)
        self.project_agents.pop(name, None)
        self.project_started.pop(name, None)

    def remember_agent(self, name: str, agent: str) -> None:
        self.project_agents[name] = resolve_agent(agent)

    def agent_of(self, name: str) -> str:
        """Der zuletzt benutzte Agent, oder '' fuer 'nie ueber HQ gestartet'."""
        return self.project_agents.get(name, "")

    def remember_started(self, name: str, when: float) -> None:
        self.project_started[name] = when

    def started_of(self, name: str) -> float:
        """Wann das Projekt zuletzt ueber HQ gestartet wurde, oder 0.0."""
        return self.project_started.get(name, 0.0)

    def toggle_favorite(self, name: str) -> bool:
        if name in self.favorites:
            self.favorites.remove(name)
            return False
        self.favorites.append(name)
        return True

    def is_favorite(self, name: str) -> bool:
        return name in self.favorites
