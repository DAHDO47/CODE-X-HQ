"""Aktionen auf einem Projekt: starten, umbenennen, löschen, öffnen.

Bewusst ohne Qt-Importe. Alle Betriebssystemaufrufe liegen in kleinen
Hilfsfunktionen (`_spawn`, `send_to_trash`), damit die Logik davor
testbar bleibt.
"""

from __future__ import annotations

import ctypes
import os
import shutil
import subprocess
import time
from ctypes import wintypes
from pathlib import Path

from . import activity, theme
from .i18n import tr
from .config import (
    AGENT_LABELS,
    DEFAULT_AGENT,
    DEFAULT_CONSOLE_STYLE,
    DEFAULT_SHELL,
    Config,
    resolve_agent,
    resolve_shell,
)
from .scanner import NOTE_NAME, Project

FORBIDDEN_CHARS = '<>:"/\\|?*'
RESERVED_NAMES = {"CON", "PRN", "AUX", "NUL"} | {
    f"{prefix}{i}" for prefix in ("COM", "LPT") for i in range(1, 10)
}



def _osc(code: int, colour: str) -> str:
    """Eine OSC-Sequenz, mit der eine Konsole ihre eigenen Farben setzt."""
    return f"]{code};{colour}\\"


#: Vorspann fuer das CRT-Design: OSC 11 setzt den Hintergrund, OSC 10 die
#: Schrift, beide in den Farben aus `theme`. `cls` malt danach neu - und
#: wischt die Sequenz weg, falls eine alte Konsole sie nicht versteht und
#: stattdessen als Text ausgibt.
CRT_PROLOG = f"echo {_osc(11, theme.BG)}{_osc(10, theme.GREEN)}&cls"


#: Die Schalter, mit denen ein Agent ohne Rueckfragen arbeitet: kein
#: Nachfragen vor Dateiaenderungen oder Befehlen. Claude ueberspringt die
#: Berechtigungen, Codex verlaesst zusaetzlich seine Sandbox.
SKIP_PERMISSIONS_FLAG = "--dangerously-skip-permissions"
FREE_FLAGS = {
    "claude": SKIP_PERMISSIONS_FLAG,
    "codex": "--sandbox danger-full-access --ask-for-approval never",
}


def agent_line(agent: str, skip_permissions: bool = False) -> str:
    """Was in der Konsole laeuft: der Agent, auf Wunsch ohne Rueckfragen."""
    agent = resolve_agent(agent)
    return f"{agent} {FREE_FLAGS[agent]}" if skip_permissions else agent


def _ps_osc(code: int, colour: str) -> str:
    """Dieselbe OSC-Sequenz wie `_osc`, als PowerShell-Ausdruck.

    Windows PowerShell 5.1 kennt kein `` `e ``; das Escape-Zeichen entsteht
    ueber `[char]27`. In einfachen Anfuehrungszeichen ist der Backslash
    ein gewoehnliches Zeichen, und doppelte kommen gar nicht vor - die
    Zeile muss beim Start als Administrator selbst in welche.
    """
    return f"[char]27+']{code};{colour}'+[char]27+'\\'"


def ps_crt_prolog() -> str:
    """Der CRT-Vorspann fuer PowerShell.

    `CRT_PROLOG` ist cmd-Syntax; PowerShell verweigert schon das `&`.
    """
    return (
        f"Write-Host -NoNewline ({_ps_osc(11, theme.BG)}+{_ps_osc(10, theme.GREEN)})"
        "; Clear-Host"
    )


def agent_command(
    agent: str,
    style: str,
    shell: str = DEFAULT_SHELL,
    skip_permissions: bool = False,
) -> list[str]:
    """Startbefehl fuer ein Projekt: Konsole im Projektordner, darin `agent`.

    `shell` bestimmt, ob `cmd` oder PowerShell die Konsole stellt. `/K`
    bzw. `-NoExit` halten das Fenster offen, wenn der Agent beendet wird;
    `-NoExit` muss vor `-Command` stehen, alles danach gilt als Skript.
    Im CRT-Design faerbt sich die Konsole zuvor selbst; das gilt fuer
    jeden Agenten gleich, er aendert nur, was darin laeuft.

    Weder ein unbekanntes Design, eine unbekannte Shell noch ein
    unbekannter Agent verweigern den Start: alle fallen auf die Vorgabe
    zurueck. In der `config.json` kann von Hand stehen, was will.
    """
    line = agent_line(agent, skip_permissions)
    if resolve_shell(shell) == "powershell":
        script = f"{ps_crt_prolog()}; {line}" if style == "crt" else line
        return ["powershell", "-NoExit", "-Command", script]
    if style == "crt":
        return ["cmd", "/K", f"{CRT_PROLOG}&{line}"]
    return ["cmd", "/K", line]


class RunnerError(Exception):
    """Fehler mit einer für den Nutzer lesbaren Meldung."""


# --- Betriebssystem-Randschicht -------------------------------------------


#: Variablen, die eine laufende Claude-Sitzung ihren Kindprozessen
#: mitgibt. Wird der Launcher selbst aus einer solchen Sitzung gestartet,
#: erbt er sie - und ohne Zutun jede Konsole, die er oeffnet. Das Claude
#: darin haelt sich dann fuer eine Unter-Sitzung und schreibt kein
#: Transcript mehr. Die Liste ist bewusst namentlich und kein
#: `CLAUDE*`-Kahlschlag: was der Nutzer selbst dauerhaft gesetzt hat
#: (`ANTHROPIC_API_KEY`, eigene `CLAUDE_CODE_*`-Schalter), muss durch.
SESSION_MARKERS = (
    "CLAUDECODE",
    "CLAUDE_CODE_CHILD_SESSION",
    "CLAUDE_CODE_SESSION_ID",
    "CLAUDE_CODE_BRIDGE_SESSION_ID",
    "CLAUDE_CODE_MESSAGING_SOCKET",
    "CLAUDE_CODE_MESSAGING_TOKEN",
    "CLAUDE_CODE_ENTRYPOINT",
    "CLAUDE_PID",
)


def _child_env() -> dict[str, str]:
    """Die eigene Umgebung, ohne geerbte Sitzungsmarker."""
    return {k: v for k, v in os.environ.items() if k not in SESSION_MARKERS}


def _elevated_params(args: list[str], cwd: Path) -> str:
    r"""Die Kommandozeile fuer die erhoehte Konsole - als Zeile, nicht als Liste.

    Zwei Dinge, die der erhoehte Prozess nicht von uns bekommt, stehen
    deshalb im Befehl selbst:

    Der Ordner. `ShellExecuteW` nimmt einen entgegen, benutzt ihn beim
    Verb 'runas' aber nicht: gestartet wird der Prozess nicht von uns,
    sondern vom Dienst hinter der Rechteerhoehung, und der setzt sein
    eigenes Verzeichnis. Gemessen landete die Konsole in
    C:\Windows\System32 - egal, welches Projekt gemeint war. `cd /d`
    wechselt Ordner und Laufwerk in einem, das Projekt liegt auf D:.

    Die Sitzungsmarker. `_child_env` greift aus demselben Grund nicht;
    `set NAME=` ohne Wert loescht eine Variable in der Konsole selbst.
    Das Aufraeumen kommt nach dem Wechsel, damit es dort geschieht, wo
    danach gearbeitet wird.

    Gequotet wird von Hand statt mit `list2cmdline`: das schuetzt
    Anfuehrungszeichen im Inneren mit einem Backslash, und den liest `cmd`
    nicht als Schutz, sondern als Zeichen. Die aeussere Klammer darf `cmd`
    dagegen abziehen - bei mehr als zwei Anfuehrungszeichen streicht es
    genau das erste und das letzte und fuehrt den Rest aus.
    """
    chain = [f'cd /d "{cwd}"']
    chain += [f"set {name}=" for name in SESSION_MARKERS if name in os.environ]
    # Ohne `/K`-Kette gibt es keinen Befehl, den die Konsole ausfuehren
    # soll - dann bleibt es beim Wechsel, und die Konsole steht offen.
    if len(args) > 2 and args[1] == "/K":
        chain.append(args[2])
    return '/K "' + "&".join(chain) + '"'


def _elevated_ps_params(args: list[str], cwd: Path) -> str:
    """Wie `_elevated_params`, nur fuer PowerShell statt cmd.

    `Set-Location` wechselt auch das Laufwerk. Der Ordner steht in
    einfachen Anfuehrungszeichen, ein Apostroph darin wird verdoppelt;
    doppelte Anfuehrungszeichen kann ein Windows-Pfad nicht enthalten.
    """
    folder = str(cwd).replace("'", "''")
    chain = [f"Set-Location -LiteralPath '{folder}'"]
    chain += [
        f"Remove-Item Env:{name} -ErrorAction SilentlyContinue"
        for name in SESSION_MARKERS
        if name in os.environ
    ]
    chain.append(args[-1])
    return '-NoExit -Command "' + "; ".join(chain) + '"'


#: Rueckgabewerte von `ShellExecuteW`. Alles bis 32 ist ein Fehler; 5 heisst,
#: dass der Nutzer den UAC-Dialog mit 'Nein' beantwortet hat.
SW_SHOWNORMAL = 1
SE_ERR_ACCESSDENIED = 5


def _shell_execute(program: str, params: str, cwd: str) -> int:
    """`ShellExecuteW` mit dem Verb 'runas' - der einzige Weg zu UAC."""
    return ctypes.windll.shell32.ShellExecuteW(
        None, "runas", program, params, cwd, SW_SHOWNORMAL
    )


def _spawn_elevated(args: list[str], cwd: Path) -> None:
    """Startet dasselbe Programm, nur mit erhoehten Rechten.

    `subprocess.Popen` kann nicht erhoehen: der neue Prozess erbt das Token
    des alten. Unter Windows fuehrt daran nur `ShellExecuteW` mit dem Verb
    'runas' vorbei, und das nimmt eine Kommandozeile statt einer Liste.
    Gebaut wird sie in `_elevated_params`; dort steht auch, was der
    erhoehte Prozess sonst noch nicht von uns erbt.
    """
    build = _elevated_ps_params if args[0] == "powershell" else _elevated_params
    result = _shell_execute(args[0], build(args, cwd), str(cwd))
    if result == SE_ERR_ACCESSDENIED:
        raise RunnerError(tr("Der Start als Administrator wurde abgelehnt."))
    if result <= 32:
        raise RunnerError(
            tr("Start als Administrator fehlgeschlagen (Code {code}).", code=result)
        )


def _spawn(args: list[str], cwd: Path, *, console: bool = True) -> None:
    """Startet ein Programm im Ordner `cwd`.

    Die Argumente werden als Liste uebergeben, nie als zusammengesetzter
    String mit `shell=True`: Windows uebernimmt so das Quoting selbst.
    Ein Pfad mit Leerzeichen kann damit nicht mehr an eigenen
    Anfuehrungszeichen zerbrechen.

    Scheitert der Start, wird daraus ein `RunnerError`. Ungefangen schluege
    der `OSError` bis in den Qt-Slot durch, und weil die .exe ohne Konsole
    laeuft, gaebe es keinen Ort, an dem der Traceback sichtbar wuerde: der
    Knopf taete kommentarlos nichts.
    """
    try:
        subprocess.Popen(
            args,
            cwd=str(cwd),
            env=_child_env(),
            creationflags=subprocess.CREATE_NEW_CONSOLE if console else 0,
        )
    except OSError as exc:
        raise RunnerError(
            tr("Start fehlgeschlagen: {reason}", reason=exc.strerror or exc)
        ) from exc


class _SHFILEOPSTRUCTW(ctypes.Structure):
    _fields_ = [
        ("hwnd", wintypes.HWND),
        ("wFunc", wintypes.UINT),
        ("pFrom", wintypes.LPCWSTR),
        ("pTo", wintypes.LPCWSTR),
        ("fFlags", ctypes.c_uint16),
        ("fAnyOperationsAborted", wintypes.BOOL),
        ("hNameMappings", ctypes.c_void_p),
        ("lpszProgressTitle", wintypes.LPCWSTR),
    ]


FO_DELETE = 3
FOF_SILENT = 0x0004
FOF_NOCONFIRMATION = 0x0010
FOF_ALLOWUNDO = 0x0040


def send_to_trash(path: Path) -> None:
    """Verschiebt den Ordner in den Windows-Papierkorb."""
    op = _SHFILEOPSTRUCTW(
        hwnd=None,
        wFunc=FO_DELETE,
        pFrom=str(Path(path).resolve()) + "\0\0",
        pTo=None,
        fFlags=FOF_ALLOWUNDO | FOF_NOCONFIRMATION | FOF_SILENT,
        fAnyOperationsAborted=False,
        hNameMappings=None,
        lpszProgressTitle=None,
    )
    result = ctypes.windll.shell32.SHFileOperationW(ctypes.byref(op))
    if result != 0:
        raise RunnerError(
            tr("Papierkorb-Vorgang fehlgeschlagen (Code {code}).", code=result)
        )


# --- Aktionen -------------------------------------------------------------


def start(
    project: Project,
    agent: str = DEFAULT_AGENT,
    style: str = DEFAULT_CONSOLE_STYLE,
    admin: bool = False,
    skip_permissions: bool = False,
    shell: str = DEFAULT_SHELL,
) -> None:
    """Oeffnet eine Konsole im Projektordner und startet darin `agent`.

    Fuer jedes Projekt derselbe Befehl. Was im Ordner liegt, spielt keine
    Rolle. `agent` bestimmt, was laeuft, `style` nur, wie die Konsole
    dabei aussieht, `shell` nur, ob `cmd` oder PowerShell sie stellt, und
    `admin` nur, mit welchen Rechten.

    `skip_permissions` haengt die Schalter aus `FREE_FLAGS` an: Claude
    fragt dann nicht mehr nach, Codex laeuft ausserdem ohne Sandbox.

    Fehlt der gewaehlte Agent, wird das hier gemeldet - und zwar unter
    seinem Namen. Sonst ginge eine Konsole auf, in der Windows erklaert,
    der Befehl sei falsch geschrieben, und die bliebe wegen `/K` stehen.
    """
    if not project.path.is_dir():
        raise RunnerError(tr("Ordner '{path}' existiert nicht mehr.", path=project.path))

    # Gemeldet werden soll, was tatsaechlich fehlt - und das ist bei einem
    # unbekannten Namen die Vorgabe, nicht der Name selbst.
    agent = resolve_agent(agent)
    if not shutil.which(agent):
        raise RunnerError(
            tr(
                "{label} ('{agent}') wurde im PATH nicht gefunden.",
                label=AGENT_LABELS[agent],
                agent=agent,
            )
        )
    command = agent_command(agent, style, shell, skip_permissions)
    if admin:
        _spawn_elevated(command, project.path)
    else:
        _spawn(command, project.path)


def validate_name(new_name: str, parent: Path, current: Path | None = None) -> None:
    """Prueft einen Ordnernamen unterhalb von `parent`.

    `current` ist der Ordner, der gerade umbenannt wird. Er darf sich
    selbst nicht im Weg stehen; beim Anlegen bleibt er leer.
    """
    name = new_name.strip()
    if not name:
        raise RunnerError(tr("Der Name darf nicht leer sein."))
    bad = [c for c in FORBIDDEN_CHARS if c in name]
    if bad:
        raise RunnerError(tr("Unerlaubte Zeichen: {chars}", chars=" ".join(bad)))
    if name.rstrip(". ") != name:
        raise RunnerError(
            tr("Der Name darf nicht mit Punkt oder Leerzeichen enden.")
        )
    if name.split(".")[0].upper() in RESERVED_NAMES:
        raise RunnerError(tr("'{name}' ist ein reservierter Windows-Name.", name=name))

    target = Path(parent) / name
    if target.exists() and (current is None or target.resolve() != current.resolve()):
        raise RunnerError(tr("'{name}' existiert bereits.", name=name))


def create(root: Path, name: str) -> Path:
    """Legt einen neuen, leeren Projektordner an und gibt seinen Pfad zurueck."""
    root = Path(root)
    if not root.is_dir():
        raise RunnerError(tr("Projektordner '{path}' existiert nicht.", path=root))
    validate_name(name, root)
    target = root / name.strip()
    try:
        target.mkdir()
    except OSError as exc:
        raise RunnerError(
            tr("Anlegen fehlgeschlagen: {reason}", reason=exc.strerror or exc)
        ) from exc
    return target


def rename(project: Project, new_name: str, config: Config) -> Path:
    validate_name(new_name, project.path.parent, project.path)
    name = new_name.strip()
    target = project.path.parent / name
    try:
        project.path.rename(target)
    except OSError as exc:
        raise RunnerError(
            tr("Umbenennen fehlgeschlagen: {reason}", reason=exc.strerror or exc)
        ) from exc

    config.rename_entry(project.name, name)
    project.name = name
    project.path = target
    return target


def delete(project: Project, config: Config) -> None:
    if not project.path.is_dir():
        raise RunnerError(tr("Ordner '{path}' existiert nicht mehr.", path=project.path))
    send_to_trash(project.path)
    # Alles, was unter diesem Namen gemerkt war, faellt mit weg - sonst
    # erbte ein spaeter gleichnamiges Projekt die Eintraege.
    config.forget(project.name)


def open_explorer(project: Project) -> None:
    if not project.path.is_dir():
        raise RunnerError(tr("Ordner '{path}' existiert nicht mehr.", path=project.path))
    try:
        os.startfile(str(project.path))
    except OSError as exc:
        raise RunnerError(
            tr("Ordner laesst sich nicht oeffnen: {reason}", reason=exc.strerror or exc)
        ) from exc


def open_terminal(
    project: Project, style: str = DEFAULT_CONSOLE_STYLE, admin: bool = False
) -> None:
    """Oeffnet eine Konsole im Projektordner - ohne Agent darin.

    Dieselbe Konsole wie beim Start, nur laeuft nichts darin. Im CRT-Design
    bekommt sie denselben Farbvorspann.

    Windows Terminal wird bewusst nicht mehr bevorzugt, obwohl es meist
    installiert ist: `wt` parst die uebergebene Kommandozeile selbst und
    kommt mit den ESC-Sequenzen des Vorspanns nicht zurecht. Gemessen geht
    ein schlichter Befehl durch, eine &-Kette auch, der Vorspann nicht -
    dann lief gar nichts, und es ging nicht einmal ein Fenster auf. F4 tat
    im CRT-Design also nichts, und das ist die Vorgabe.
    """
    if not project.path.is_dir():
        raise RunnerError(tr("Ordner '{path}' existiert nicht mehr.", path=project.path))
    command = ["cmd", "/K", CRT_PROLOG] if style == "crt" else ["cmd"]
    if admin:
        _spawn_elevated(command, project.path)
    else:
        _spawn(command, project.path)


#: Die Ueberschrift, unter der alles in der Notiz steht. Sie ist zugleich
#: die Marke, an der `insert_status` erkennt, wo ein neuer Block hingehoert.
NOTE_HEADING = "# Aufgaben — {name}"


def note_path(project: Project) -> Path:
    """Wo die Notiz eines Projekts liegt - im Projektordner selbst."""
    return project.path / NOTE_NAME


def _status(project: Project) -> str:
    """Der Stand des Projekts - oder nichts, wenn er sich nicht erheben laesst.

    `activity` liest Sitzungsarchive in einem undokumentierten Format.
    Aendert es sich, ist das kein Grund, warum ein Klick auf das
    Notizsymbol scheitern sollte: dann geht die Notiz eben ohne Stand auf.
    Gefangen wird bewusst alles, nicht nur `OSError` - was dort schiefgeht,
    ist nicht vorherzusehen.
    """
    try:
        return activity.status_block(project.path)
    except Exception:  # noqa: BLE001 - siehe Docstring
        return ""


def _write_note(target: Path, text: str) -> None:
    """Schreibt die Notiz, ohne das Projekt frisch aussehen zu lassen.

    Eine neue Datei ist ein neuer Eintrag im Verzeichnis, und davon hebt
    Windows die Zeit des Ordners an. `activity.newest_change` laesst die
    Notiz zwar aus, faellt aber auf die Ordnerzeit zurueck, wenn es sonst
    nichts zu sehen gibt - in einem leeren Projekt also immer. Gemessen
    sprang so ein Projekt um 60 Tage nach vorn und stand in der Liste
    ganz oben, nur weil jemand einmal auf das Notizsymbol geklickt hatte.

    Also stellt HQ den Zeitstempel hinterher wieder her: seinen eigenen
    Nebeneffekt macht es rueckgaengig, statt ihn spaeter wegzurechnen.
    Misslingt das, ist es kein Grund zu scheitern - die Notiz steht dann
    trotzdem, nur das Datum ist eine Spur zu frisch.
    """
    ordner = target.parent
    try:
        vorher = ordner.stat().st_mtime
    except OSError:
        vorher = None

    try:
        target.write_text(text, encoding="utf-8")
    except OSError as exc:
        raise RunnerError(
            tr("Notiz laesst sich nicht schreiben: {reason}", reason=exc.strerror or exc)
        ) from exc

    if vorher is not None:
        try:
            os.utime(ordner, (vorher, vorher))
        except OSError:
            pass


def _fresh_note(project: Project) -> str:
    """Eine neue Notiz: Ueberschrift und der Stand von jetzt."""
    heading = NOTE_HEADING.format(name=project.name)
    status = _status(project).strip()
    return f"{heading}\n\n{status}\n" if status else f"{heading}\n\n-\n"


def open_note(project: Project) -> Path:
    """Oeffnet die Notiz des Projekts in Notepad, legt sie notfalls an.

    Angelegt wird sie hier und nicht von Notepad: sonst fragte Notepad
    erst, ob es die Datei anlegen soll, und ein Klick auf das Symbol
    haette einen Dialog statt eines Editors zur Folge.

    Eine frisch angelegte Notiz enthaelt gleich den Stand des Projekts -
    ein leeres Blatt ist keine Hilfe. Eine vorhandene Datei wird dagegen
    nie angefasst; sonst wuchse sie bei jedem Blick hinein.

    Notepad laeuft ohne eigene Konsole - sonst blitzte bei jedem Klick ein
    schwarzes Fenster auf.
    """
    if not project.path.is_dir():
        raise RunnerError(tr("Ordner '{path}' existiert nicht mehr.", path=project.path))

    target = note_path(project)
    if not target.exists():
        _write_note(target, _fresh_note(project))

    _spawn(["notepad", str(target)], project.path, console=False)
    return target


def with_status_on_top(text: str, block: str, name: str) -> str:
    """Setzt `block` unter die Ueberschrift, alles Bisherige darunter.

    Oben und nicht unten: in Notepad steht das Neueste damit ohne Scrollen
    da. Getrennt von `insert_status`, damit sich das Zusammensetzen ohne
    Dateien und ohne Editor pruefen laesst.

    Fehlt die Ueberschrift - von Hand angelegt, aus einer Vorversion -,
    kommt eine davor, und der vorhandene Text rutscht mit nach unten,
    statt unter die neue Ueberschrift zu geraten und dort zu verschwinden.
    """
    heading = NOTE_HEADING.format(name=name)
    lines = text.splitlines()
    if lines and lines[0].startswith("# "):
        heading, lines = lines[0], lines[1:]

    rest = "\n".join(lines).strip("\n")
    result = f"{heading}\n\n{block.strip()}\n"
    return f"{result}\n{rest}\n" if rest else result


def insert_status(project: Project) -> Path:
    """Schreibt den aktuellen Stand oben in die Notiz und oeffnet sie.

    Anders als `open_note` auch dann, wenn die Notiz schon da ist - das
    ist der Sinn: die Datei wird zu einem kleinen Verlauf.
    """
    if not project.path.is_dir():
        raise RunnerError(tr("Ordner '{path}' existiert nicht mehr.", path=project.path))

    target = note_path(project)
    block = _status(project) or "## Kein Stand zu ermitteln"
    try:
        vorhanden = target.read_text(encoding="utf-8") if target.exists() else ""
    except OSError as exc:
        raise RunnerError(
            tr("Notiz laesst sich nicht lesen: {reason}", reason=exc.strerror or exc)
        ) from exc

    _write_note(target, with_status_on_top(vorhanden, block, project.name))
    _spawn(["notepad", str(target)], project.path, console=False)
    return target


def open_vscode(project: Project) -> None:
    if not shutil.which("code"):
        raise RunnerError(tr("VS Code ('code') wurde im PATH nicht gefunden."))
    # `code` ist eine .cmd und laeuft daher ueber den Kommandointerpreter.
    # Ohne eigene Konsole, sonst blitzt beim Oeffnen ein Fenster auf.
    _spawn(["cmd", "/C", "code", str(project.path)], project.path, console=False)


def _system_dir() -> Path:
    """Ein Ordner, der immer existiert - `shutdown` braucht keinen bestimmten."""
    return Path(os.environ.get("SystemRoot", r"C:\Windows"))


def schedule_shutdown(minutes: float) -> None:
    """Plant, dass der Rechner in `minutes` Minuten herunterfaehrt.

    Laeuft ueber das Windows-Bordmittel `shutdown /t`, nicht ueber einen
    eigenen Timer in HQ: der Countdown laeuft so auch weiter, wenn HQ
    zwischendurch geschlossen wird.
    """
    seconds = max(0, round(minutes * 60))
    _spawn(["shutdown", "/s", "/t", str(seconds)], _system_dir(), console=False)


def cancel_shutdown() -> None:
    """Bricht ein geplantes Herunterfahren wieder ab."""
    _spawn(["shutdown", "/a"], _system_dir(), console=False)


# --- Hilfsfunktionen ------------------------------------------------------


#: Wie lange und ueber wie viele Dateien die Groesse hoechstens gezaehlt
#: wird. Der Loeschen-Dialog rechnet sie im Oberflaechen-Thread aus; ohne
#: Budget stuende das Fenster bei einem Projekt mit node_modules mehrere
#: Sekunden still, bevor ueberhaupt etwas erscheint. Fuer die Frage, die
#: der Dialog stellt, genuegt eine Untergrenze.
SIZE_TIME_BUDGET = 0.3
SIZE_FILE_BUDGET = 20_000


def folder_size(
    path: Path,
    *,
    time_budget: float = SIZE_TIME_BUDGET,
    file_budget: int = SIZE_FILE_BUDGET,
) -> tuple[int, bool]:
    """(Summe der Dateigroessen, ob zu Ende gezaehlt wurde).

    Ist eines der Budgets erschoepft, bricht die Zaehlung ab. Die Summe
    ist dann eine Untergrenze, und der zweite Wert sagt es.
    """
    total = 0
    counted = 0
    deadline = time.monotonic() + time_budget
    for current, _dirs, files in os.walk(path):
        for filename in files:
            if counted >= file_budget or time.monotonic() >= deadline:
                return total, False
            counted += 1
            try:
                total += (Path(current) / filename).stat().st_size
            except OSError:
                continue
    return total, True


def size_label(path: Path, **budget) -> str:
    """Die Ordnergroesse als Text, mit '>' davor bei abgebrochener Zaehlung."""
    total, complete = folder_size(path, **budget)
    return human_size(total) if complete else f"> {human_size(total)}"


def human_size(num_bytes: int) -> str:
    if num_bytes < 1024:
        return f"{num_bytes} B"
    value = float(num_bytes)
    for unit in ("KB", "MB", "GB", "TB"):
        value /= 1024
        if value < 1024:
            return f"{value:.1f} {unit}"
    return f"{value:.1f} PB"
