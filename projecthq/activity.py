"""Was in einem Projekt zuletzt geschehen ist.

Vier Quellen, aus denen sich der Stand eines Projekts ablesen laesst:
die Sitzungen von Claude und Codex, die letzten Commits und die zuletzt
geaenderten Dateien. Zusammengesetzt werden sie in `status_block`, und
`runner` schreibt das Ergebnis in die Notiz des Projekts.

Bewusst ohne Qt, wie `config`, `scanner` und `runner`.

Zwei Dinge bestimmen den Zuschnitt dieses Moduls:

**Nichts hier darf nach oben durchschlagen.** Die Sitzungsdateien von
Claude und Codex sind ein undokumentiertes Format; aendert es sich, ist
das kein Grund, warum ein Klick auf das Notizsymbol scheitern sollte.
Jede Quelle faengt ihre Fehler selbst und liefert dann nichts - der
Abschnitt fehlt in der Notiz, mehr passiert nicht.

**Nichts hier darf lange dauern.** Der Codex-Ordner hatte bei der
Messung 99 Sitzungen, einzelne ueber 5 MB. Deshalb Budgets wie bei
`runner.folder_size`: gelesen wird, was in der Zeit zu schaffen ist.
Aufgerufen wird das Ganze ohnehin nur beim Anlegen einer Notiz und beim
Einfuegen eines Standes - nie beim Scannen der Liste.
"""

from __future__ import annotations

import json
import os
import subprocess
import time
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

from .scanner import NOTE_NAME

#: Wo die beiden Werkzeuge ihre Sitzungen ablegen. Als Modulvariablen und
#: nicht als Konstanten in den Funktionen: die Tests legen sie um, statt
#: das Benutzerprofil anzufassen.
CLAUDE_ROOT = Path.home() / ".claude" / "projects"
CODEX_ROOT = Path.home() / ".codex" / "sessions"

#: Wie lange in den Sitzungsarchiven gesucht wird. Lieber ein
#: unvollstaendiger Abschnitt als ein Fenster, das steht.
SESSION_TIME_BUDGET = 2.0

#: Ordner, die in "zuletzt geaendert" nichts zu suchen haben: sonst
#: stuenden dort nur Build-Erzeugnisse und Paketverzeichnisse.
SKIP_DIRS = frozenset(
    {
        ".git",
        ".svn",
        ".hg",
        ".venv",
        "venv",
        "node_modules",
        "__pycache__",
        ".pytest_cache",
        ".mypy_cache",
        ".idea",
        ".vscode",
        "build",
        "dist",
        "obj",
        "bin",
        "target",
    }
)

#: Budget fuer den Durchlauf durch den Projektordner, aus demselben Grund
#: wie bei `runner.folder_size`: ein Projekt mit node_modules haette sonst
#: kein absehbares Ende.
WALK_TIME_BUDGET = 0.5
WALK_FILE_BUDGET = 5_000

#: So lang darf ein Thema in der Notiz werden. Eine Frage an Claude kann
#: mehrere Absaetze haben; in der Liste steht davon der Anfang.
TOPIC_LIMIT = 70


@dataclass(frozen=True)
class Entry:
    """Ein Ereignis: wann, was, und woher es stammt."""

    when: float
    what: str
    source: str = ""


def _shorten(text: str, limit: int = TOPIC_LIMIT) -> str:
    """Eine Zeile daraus machen, notfalls gekuerzt."""
    text = " ".join(text.split())
    if len(text) <= limit:
        return text
    return text[: limit - 1].rstrip() + "…"


def _looks_injected(text: str) -> bool:
    """Ob der Text vom Werkzeug stammt und nicht vom Nutzer.

    Claude schiebt Erinnerungen, Hinweise und den Inhalt aufgerufener
    Faehigkeiten als Nutzernachrichten in das Protokoll. In der Notiz
    haetten sie nichts verloren - gesucht ist, was der Mensch wollte.
    """
    anfang = text.lstrip()[:40]
    return (
        anfang.startswith("<")
        or anfang.startswith("Caveat:")
        or anfang.startswith("Base directory for this skill")
        or anfang.startswith("[Request interrupted")
    )


# --- Claude ---------------------------------------------------------------


def claude_folder_name(path: Path) -> str:
    """Der Ordnername, unter dem Claude die Sitzungen eines Pfades ablegt.

    Aus `D:\\Projekte\\HQ` wird `D--Projekte-HQ`. Die
    Regel ist abgelesen, nicht dokumentiert - und sie ist nicht eindeutig:
    'Mein Projekt' und 'Mein-Projekt' ergeben denselben Namen. Deshalb
    dient sie nur zum Finden; entschieden wird am `cwd`, das in der Datei
    selbst steht.
    """
    name = str(Path(path))
    for zeichen in (":", "\\", "/", " ", "_", "."):
        name = name.replace(zeichen, "-")
    return name


def _claude_folder(path: Path) -> Path | None:
    """Der Ordner mit den Sitzungen zu `path`, sofern es einen gibt."""
    try:
        kandidat = CLAUDE_ROOT / claude_folder_name(path)
        return kandidat if kandidat.is_dir() else None
    except OSError:
        return None


def _read_claude_session(datei: Path, erwartet: str) -> Entry | None:
    """Titel und Zeitpunkt einer Sitzung, falls sie zu `erwartet` gehoert.

    Gelesen wird zeilenweise mit einer billigen Vorpruefung: die Dateien
    werden ueber ein Megabyte gross, und `json.loads` auf jede Zeile
    kostet mehr als ein `in` auf den Rohtext.

    Der Titel, den Claude selbst vergibt, ist die beste Zusammenfassung,
    die zu haben ist. Eine ganz frische Sitzung hat noch keinen - dann
    tut es die erste Frage des Nutzers.
    """
    titel: str | None = None
    erste_frage: str | None = None
    passt: bool | None = None

    try:
        with datei.open(encoding="utf-8", errors="replace") as fh:
            for zeile in fh:
                if passt is None and '"cwd"' in zeile:
                    satz = _json(zeile)
                    cwd = satz.get("cwd") if satz else None
                    if isinstance(cwd, str):
                        passt = Path(cwd) == Path(erwartet)
                        if not passt:
                            return None
                if "ai-title" in zeile:
                    satz = _json(zeile)
                    wert = satz.get("aiTitle") if satz else None
                    if isinstance(wert, str) and wert.strip():
                        titel = wert.strip()
                elif erste_frage is None and '"user"' in zeile:
                    text = _claude_prompt(zeile)
                    if text:
                        erste_frage = text
    except OSError:
        return None

    if not passt:
        return None
    thema = titel or erste_frage
    if not thema:
        return None
    try:
        wann = datei.stat().st_mtime
    except OSError:
        return None
    return Entry(when=wann, what=_shorten(thema), source="Claude")


def _json(zeile: str) -> dict | None:
    try:
        satz = json.loads(zeile)
    except (ValueError, TypeError):
        return None
    return satz if isinstance(satz, dict) else None


def _claude_prompt(zeile: str) -> str | None:
    """Die Nutzerfrage aus einem `user`-Satz, sofern es eine echte ist."""
    satz = _json(zeile)
    if not satz or satz.get("type") != "user":
        return None
    inhalt = (satz.get("message") or {}).get("content")
    if isinstance(inhalt, list):
        inhalt = " ".join(
            teil.get("text", "")
            for teil in inhalt
            if isinstance(teil, dict) and teil.get("type") == "text"
        )
    if not isinstance(inhalt, str) or not inhalt.strip():
        return None
    if _looks_injected(inhalt):
        return None
    return inhalt.strip()


def claude_sessions(path: Path, limit: int = 5) -> list[Entry]:
    """Die juengsten Claude-Sitzungen zu diesem Projekt, neueste zuerst."""
    ordner = _claude_folder(Path(path))
    if ordner is None:
        return []
    try:
        dateien = sorted(
            ordner.glob("*.jsonl"), key=lambda f: f.stat().st_mtime, reverse=True
        )
    except OSError:
        return []

    frist = time.monotonic() + SESSION_TIME_BUDGET
    gefunden: list[Entry] = []
    for datei in dateien:
        if len(gefunden) >= limit or time.monotonic() >= frist:
            break
        eintrag = _read_claude_session(datei, str(Path(path)))
        if eintrag is not None:
            gefunden.append(eintrag)
    return gefunden


# --- Codex ----------------------------------------------------------------


def _codex_belongs_to(datei: Path, erwartet: Path) -> bool:
    """Ob eine Codex-Sitzung in diesem Projekt lief.

    Codex legt nach Datum ab, nicht nach Projekt - der Ordner steht im
    Kopfsatz. Gelesen wird deshalb nur die erste Zeile; bei knapp hundert
    Sitzungen, von denen einzelne ueber 5 MB haben, ist das der
    Unterschied zwischen sofort und spuerbar.
    """
    try:
        with datei.open(encoding="utf-8", errors="replace") as fh:
            kopf = _json(fh.readline())
    except OSError:
        return False
    if not kopf:
        return False
    cwd = (kopf.get("payload") or {}).get("cwd")
    if not isinstance(cwd, str):
        return False
    # Gross- und Kleinschreibung sind unter Windows dasselbe Laufwerk.
    return str(Path(cwd)).casefold() == str(erwartet).casefold()


def _codex_text(payload: dict) -> str | None:
    """Die Nutzernachricht aus einem Codex-Satz - beide Formate.

    Codex hat sein Protokoll zwischen Mai und September 2026 umgestellt,
    und beide Formen liegen nebeneinander im Archiv:

    neu   `event_msg` -> `item_completed` -> `item.type == "UserMessage"`
    alt   `response_item` -> `message` mit `role == "user"` und
          `content` als Liste von `input_text`-Stuecken

    Wer nur die neue Form liest, sieht bei aelteren Projekten nichts -
    gemessen an 'Notizen': 13 Sitzungen, alle in der alten Form.
    """
    eintrag = payload.get("item")
    if isinstance(eintrag, dict) and eintrag.get("type") == "UserMessage":
        roh = eintrag.get("text") or eintrag.get("content") or ""
    elif payload.get("type") == "message" and payload.get("role") == "user":
        roh = payload.get("content") or ""
    else:
        return None

    if isinstance(roh, list):
        roh = " ".join(t.get("text", "") for t in roh if isinstance(t, dict))
    if not isinstance(roh, str) or not roh.strip() or _looks_injected(roh):
        return None
    return roh.strip()


def _codex_first_prompt(datei: Path) -> str | None:
    try:
        with datei.open(encoding="utf-8", errors="replace") as fh:
            for zeile in fh:
                # Billige Vorpruefung: die Dateien werden mehrere Megabyte
                # gross, und `json.loads` je Zeile kostet ein Vielfaches.
                if "UserMessage" not in zeile and '"user"' not in zeile:
                    continue
                satz = _json(zeile)
                payload = (satz or {}).get("payload")
                if not isinstance(payload, dict):
                    continue
                text = _codex_text(payload)
                if text:
                    return text
    except OSError:
        return None
    return None


def codex_sessions(path: Path, limit: int = 5) -> list[Entry]:
    """Die juengsten Codex-Sitzungen zu diesem Projekt, neueste zuerst."""
    path = Path(path)
    try:
        if not CODEX_ROOT.is_dir():
            return []
        dateien = sorted(
            CODEX_ROOT.rglob("*.jsonl"),
            key=lambda f: f.stat().st_mtime,
            reverse=True,
        )
    except OSError:
        return []

    frist = time.monotonic() + SESSION_TIME_BUDGET
    gefunden: list[Entry] = []
    for datei in dateien:
        if len(gefunden) >= limit or time.monotonic() >= frist:
            break
        if not _codex_belongs_to(datei, path):
            continue
        thema = _codex_first_prompt(datei)
        if not thema:
            continue
        try:
            wann = datei.stat().st_mtime
        except OSError:
            continue
        gefunden.append(Entry(when=wann, what=_shorten(thema), source="Codex"))
    return gefunden


def sessions(path: Path, limit: int = 5) -> list[Entry]:
    """Claude und Codex in einer Liste, neueste zuerst."""
    beide = claude_sessions(path, limit) + codex_sessions(path, limit)
    return sorted(beide, key=lambda e: e.when, reverse=True)[:limit]


# --- Git ------------------------------------------------------------------

#: Ohne dieses Flag blitzt bei jedem Aufruf eine Konsole auf - die .exe
#: laeuft ohne eigene. Auf anderen Systemen gibt es das Flag nicht.
NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)

#: Ein haengendes `git` darf das Fenster nicht mitreissen.
GIT_TIMEOUT = 3.0


def _git(path: Path, *args: str) -> str | None:
    """Ruft git im Projektordner auf. `None`, wenn dabei irgendetwas schiefgeht."""
    if not (Path(path) / ".git").exists():
        return None
    try:
        fertig = subprocess.run(
            ["git", *args],
            cwd=str(path),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=GIT_TIMEOUT,
            creationflags=NO_WINDOW,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    return fertig.stdout if fertig.returncode == 0 else None


def git_commits(path: Path, limit: int = 5) -> list[str]:
    """Die letzten Commit-Zeilen, neueste zuerst."""
    ausgabe = _git(path, "log", f"-{limit}", "--oneline", "--no-decorate")
    if not ausgabe:
        return []
    return [zeile.strip() for zeile in ausgabe.splitlines() if zeile.strip()]


def git_pending(path: Path) -> str | None:
    """Wieviel unversioniert herumliegt, oder `None` bei sauberem Stand."""
    ausgabe = _git(path, "status", "--porcelain")
    if not ausgabe:
        return None

    geaendert = neu = 0
    for zeile in ausgabe.splitlines():
        if not zeile.strip():
            continue
        if zeile.startswith("??"):
            neu += 1
        else:
            geaendert += 1

    teile = []
    if geaendert:
        teile.append(f"{geaendert} geändert")
    if neu:
        teile.append(f"{neu} neu")
    return ", ".join(teile) if teile else None


# --- Zuletzt geaenderte Dateien -------------------------------------------


def recent_files(path: Path, limit: int = 5) -> list[Entry]:
    """Die zuletzt geaenderten Dateien des Projekts, neueste zuerst.

    Die einzige Quelle, die bei jedem Projekt etwas liefert - und die
    unschaerfste. Build-Erzeugnisse und Paketverzeichnisse bleiben
    draussen, sonst stuende in der Notiz nichts anderes.
    """
    wurzel = Path(path)
    if not wurzel.is_dir():
        return []

    frist = time.monotonic() + WALK_TIME_BUDGET
    gezaehlt = 0
    treffer: list[tuple[float, str]] = []
    for aktuell, ordner, dateien in os.walk(wurzel):
        # Direkt in der Liste aendern: nur so steigt os.walk nicht hinab.
        ordner[:] = [o for o in ordner if o not in SKIP_DIRS and not o.startswith(".")]
        for name in dateien:
            if gezaehlt >= WALK_FILE_BUDGET or time.monotonic() >= frist:
                ordner[:] = []
                break
            gezaehlt += 1
            # Die Notiz selbst ist nach jedem Schreiben die juengste Datei
            # und verdraengte sonst jedes Mal, worum es eigentlich geht.
            if name == NOTE_NAME:
                continue
            voll = Path(aktuell) / name
            try:
                treffer.append((voll.stat().st_mtime, str(voll.relative_to(wurzel))))
            except OSError:
                continue

    treffer.sort(reverse=True)
    return [Entry(when=w, what=n) for w, n in treffer[:limit]]


# --- Wann zuletzt etwas geschah -------------------------------------------

#: Budget fuer die Suche nach der juengsten Datei. Gemessen ueber die 24
#: Projekte: voller Durchlauf 585 ms, mit 1000 Dateien je Projekt 281 ms -
#: und in beiden Faellen dasselbe Ergebnis.
CHANGE_TIME_BUDGET = 0.1
CHANGE_FILE_BUDGET = 1_000


def newest_change(
    path: Path,
    *,
    time_budget: float = CHANGE_TIME_BUDGET,
    file_budget: int = CHANGE_FILE_BUDGET,
) -> float:
    """Wann in diesem Projekt zuletzt etwas geaendert wurde.

    Die Aenderungszeit des Ordners taugt dafuer nicht: Windows hebt sie
    nur an, wenn direkt darin ein Eintrag dazukommt, wegfaellt oder
    umbenannt wird. Wer in einer Datei tippt - erst recht in einem
    Unterordner -, ruehrt sie nicht an. Gemessen an 'Webshop':
    Ordner 02.08., juengste Datei 07.09. - 35 Tage daneben, und weil die
    Liste nach diesem Feld sortiert, stand das Projekt ganz unten,
    waehrend darin gearbeitet wurde.

    Die Ordnerzeit ist dabei der **Rueckfall**, nicht die Untergrenze.
    Sie zaehlt nur, wenn der Durchlauf nichts gefunden hat oder sein
    Budget nicht reichte - dann weiss HQ es nicht besser.

    Untergrenze waere sie das falsche Werkzeug, denn HQ selbst hebt sie
    an: die Notiz anzulegen ist ein neuer Eintrag im Verzeichnis. Gemessen
    standen 'Archiv', 'Spiel' und 'Werkzeuge' danach auf dem
    heutigen Datum und ganz oben in der Liste, ohne dass darin gearbeitet
    worden waere - die Liste haette gezeigt, wo HQ hingeschrieben hat.
    """
    wurzel = Path(path)
    try:
        ordnerzeit = wurzel.stat().st_mtime
    except OSError:
        return 0.0

    frist = time.monotonic() + time_budget
    gezaehlt = 0
    best = 0.0
    vollstaendig = True
    for aktuell, ordner, dateien in os.walk(wurzel):
        ordner[:] = [o for o in ordner if o not in SKIP_DIRS and not o.startswith(".")]
        for name in dateien:
            if gezaehlt >= file_budget or time.monotonic() >= frist:
                ordner[:] = []
                vollstaendig = False
                break
            gezaehlt += 1
            # Die Notiz zaehlt nicht: sonst schoebe jedes 'Stand einfuegen'
            # das Projekt nach oben, und die Liste zeigte, woran HQ
            # gearbeitet hat statt der Nutzer.
            if name == NOTE_NAME:
                continue
            try:
                best = max(best, (Path(aktuell) / name).stat().st_mtime)
            except OSError:
                continue

    if not vollstaendig:
        # Abgebrochen: die juengste Datei kann hinter dem Budget liegen.
        return max(best, ordnerzeit)
    return best or ordnerzeit


def agent_index(paths: Iterable[Path]) -> dict[str, tuple[str, float]]:
    """Womit in jedem der Projekte zuletzt gearbeitet wurde.

    Ein Durchgang fuer alle Projekte statt einer je Projekt: gemessen
    kostete es einzeln 2,6 s fuer 24 Projekte, hier 33 ms. Der Unterschied
    liegt am Codex-Archiv - das ist nach Datum abgelegt, nicht nach
    Projekt, und muesste sonst 24-mal durchgesehen werden.

    Fuer diese Frage genuegt die Aenderungszeit der Sitzungsdatei; ihr
    Inhalt wird nicht gelesen. Bei Codex ist nur der Kopfsatz noetig, um
    den Ordner zu erfahren.

    Der Schluessel ist der Pfad in Kleinschreibung - unter Windows sind
    'D:\\Projekte' und 'd:\\projekte' derselbe Ordner. Ein Projekt ohne
    Sitzungen taucht gar nicht auf.
    """
    ziele = {str(Path(p)).casefold(): Path(p) for p in paths}
    gefunden: dict[str, tuple[str, float]] = {}

    def merken(schluessel: str, agent: str, wann: float) -> None:
        vorher = gefunden.get(schluessel)
        if vorher is None or wann > vorher[1]:
            gefunden[schluessel] = (agent, wann)

    # Claude: ein Ordner je Projekt, der Name kommt aus dem Pfad.
    for schluessel, pfad in ziele.items():
        ordner = CLAUDE_ROOT / claude_folder_name(pfad)
        try:
            if not ordner.is_dir():
                continue
            wann = max(
                (f.stat().st_mtime for f in ordner.glob("*.jsonl")), default=0.0
            )
        except OSError:
            continue
        if wann:
            merken(schluessel, "claude", wann)

    # Codex: alles in einem Topf, der Ordner steht im Kopfsatz.
    try:
        dateien = list(CODEX_ROOT.rglob("*.jsonl")) if CODEX_ROOT.is_dir() else []
    except OSError:
        dateien = []
    for datei in dateien:
        try:
            with datei.open(encoding="utf-8", errors="replace") as fh:
                kopf = _json(fh.readline())
            wann = datei.stat().st_mtime
        except OSError:
            continue
        cwd = ((kopf or {}).get("payload") or {}).get("cwd")
        if not isinstance(cwd, str):
            continue
        schluessel = str(Path(cwd)).casefold()
        if schluessel in ziele:
            merken(schluessel, "codex", wann)

    return gefunden


class Snapshot:
    """Gemerkte Auskuenfte ueber die Projekte.

    Beides - die juengste Aenderung und der zuletzt benutzte Agent - ist
    zu teuer, um es bei jedem Fensterwechsel neu zu erheben: zusammen rund
    300 ms fuer 24 Projekte, und die Liste wird jedes Mal neu gelesen,
    wenn das Fenster nach vorn kommt.

    Deshalb wird gerechnet, was noch nicht dasteht, und sonst der gemerkte
    Wert genommen. `clear` wirft alles weg; das haengt an Strg+R. Ein
    Projekt, das der Zwischenspeicher noch nie gesehen hat - nebenher im
    Explorer entstanden -, wird berechnet, ohne dass jemand etwas druecken
    muss.
    """

    def __init__(self) -> None:
        self._changed: dict[str, float] = {}
        self._agents: dict[str, tuple[str, float]] | None = None

    def clear(self) -> None:
        self._changed.clear()
        self._agents = None

    def forget_agents(self) -> None:
        """Nur das Archiv neu befragen, die Datumssuche nicht.

        Nach einem Start ueber HQ soll die Spalte den neuen Agenten
        zeigen, ohne dass dafuer der teure Durchlauf durch alle
        Projektordner noch einmal laeuft - 33 ms statt 320 ms.
        """
        self._agents = None

    def changed(self, path: Path) -> float:
        schluessel = str(Path(path)).casefold()
        if schluessel not in self._changed:
            self._changed[schluessel] = newest_change(path)
        return self._changed[schluessel]

    def agent(self, path: Path, all_paths: Iterable[Path]) -> str:
        """Der Agent, der in `path` zuletzt lief - '' wenn keiner.

        `all_paths` sind alle Projekte: der Index entsteht in einem
        Durchgang fuer alle, deshalb muss er sie beim ersten Mal kennen.
        """
        if self._agents is None:
            self._agents = agent_index(all_paths)
        eintrag = self._agents.get(str(Path(path)).casefold())
        return eintrag[0] if eintrag else ""


# --- Der fertige Block ----------------------------------------------------


def _when(stamp: float) -> str:
    """Tag und Uhrzeit in Ortszeit.

    Die Archive schreiben UTC; hier wird ohnehin die Aenderungszeit der
    Datei benutzt, und die liefert `localtime` richtig um.
    """
    return time.strftime("%d.%m. %H:%M", time.localtime(stamp))


def _section(title: str, lines: list[str]) -> list[str]:
    """Eine Ueberschrift samt Zeilen - oder gar nichts.

    Ein Abschnitt ohne Inhalt waere schlimmer als ein fehlender: er
    verspraeche etwas, was nicht da ist.
    """
    if not lines:
        return []
    return [f"**{title}**", *lines, ""]


def status_block(path: Path, now: float | None = None) -> str:
    """Der Stand eines Projekts als Markdown-Block.

    Was keine Auskunft gibt, taucht nicht auf. Bleibt am Ende gar nichts
    uebrig, steht das ausdruecklich da - eine Ueberschrift mit Datum und
    darunter Stille waere raetselhafter als ein Satz.
    """
    path = Path(path)
    jetzt = time.time() if now is None else now
    zeilen = [f"## Stand vom {time.strftime('%d.%m.%Y, %H:%M', time.localtime(jetzt))}", ""]

    gearbeitet = [
        f"- {_when(e.when)} · {e.source} · {e.what}" for e in sessions(path)
    ]
    zeilen += _section("Woran gearbeitet wurde", gearbeitet)

    zeilen += _section(
        "Letzte Commits", [f"- {z}" for z in git_commits(path)]
    )

    offen = git_pending(path)
    if offen:
        zeilen += [f"**Nicht committet** — {offen}", ""]

    zeilen += _section(
        "Zuletzt geändert",
        [f"- {_when(e.when)} · {e.what}" for e in recent_files(path)],
    )

    if len(zeilen) == 2:
        zeilen += ["Nichts gefunden, woran HQ sich erinnern könnte.", ""]

    return "\n".join(zeilen) + "\n"
