# CODE/X HQ

Ein Launcher für Ihren Projektordner im CRT-Terminal-Look.
Zeigt alle Projekte, öffnet sie in Claude oder Codex, legt neue an, benennt
sie um und löscht sie.

**Sprachen:** Deutsch · [English](README.en.md) ·
[Bosanski / Hrvatski / Srpski](README.bhs.md) · [Türkçe](README.tr.md) ·
[Español](README.es.md)

## Starten

**Fertige Version:** unter [Releases](https://github.com/DAHDO47/CODE-X-HQ/releases/latest) die Datei `CODE-X-HQ-windows-x64.zip`
laden, entpacken und `ProjectHQ\ProjectHQ.exe` starten — Python ist dafür
nicht nötig. Beim ersten Start unter **Einstellungen** den eigenen
Projektordner wählen (Vorgabe: `%USERPROFILE%\Projekte`). `claude` bzw.
`codex` müssen installiert und im PATH sein.

Aus dem Quelltext gebaut liegt die `.exe` hier:

```
dist\ProjectHQ\ProjectHQ.exe
```

Die `.exe` an die Taskleiste anheften oder eine Verknüpfung auf den Desktop
legen. Die Boot-Sequenz lässt sich mit einem Klick oder einer Taste
überspringen; `ProjectHQ.exe --no-boot` überspringt sie dauerhaft.

## Bedienung

Alles ist mit der Maus erreichbar: Doppelklick startet ein Projekt,
Rechtsklick öffnet das Menü mit allen Aktionen, das Seitenmenü links
bietet dieselben Aktionen für den ausgewählten Eintrag.

| Taste | Aktion |
|-------|--------|
| Doppelklick / F5 | Projekt starten |
| Strg+N | Neues Projekt anlegen |
| F2 | Umbenennen |
| Entf | Löschen (in den Papierkorb) |
| F4 | Terminal im Projektordner |
| F6 | Aufgaben des Projekts in Notepad |
| Shift+F4 | Terminal als Administrator |
| Strg+D | Als Favorit anheften oder lösen |
| Strg+R | Liste neu einlesen, Datum und Agent neu erheben |
| Strg+F | In die Suche springen |
| Esc | Suche leeren, sonst schließen |

Die Suche filtert live beim Tippen, über Name **und** Typ: `node` zeigt
alle Node-Projekte. Ein Klick auf eine Spaltenüberschrift sortiert die
Liste danach.

Die Liste hat sechs Spalten:

```
 ►  PROJEKT           TYP    AGENT      NOTIZ   ERSTELLT     BEARBEITET
 *  Tarkov            node   ■ CLAUDE     ≡     28.08.2026   05.09.2026
 ►  Webshop           py     ● CODEX      ≡     24.05.2026   02.08.2026
 ►  Homepage          web    –            ·     22.06.2026   27.07.2026
```

Neu eingelesen wird mit `Strg+R` — und automatisch, sobald das Fenster
wieder in den Vordergrund kommt. Ein Ordner, der nebenher im Explorer
entsteht, steht damit sofort in der Liste. Die Auswahl bleibt dabei
erhalten.

Ein Unterschied zwischen beiden: `BEARBEITET` und `AGENT` zu erheben
kostet rund 320 ms für 24 Projekte — zu viel für jedes Alt-Tab. Der
automatische Scan nimmt deshalb die gemerkten Werte (rund 40 ms),
**`Strg+R` erhebt sie neu**. Ein Projekt, das HQ noch nie gesehen hat,
wird immer berechnet; ein frischer Ordner steht also gleich mit
richtigem Datum da.

## Wie gestartet wird

Beim Starten fragt ein Dialog, womit:

```
┌─ WOMIT STARTEN? ────────────────┐
│  > PROJEKT:  Tarkov             │
│                                 │
│   ■  CLAUDE   Claude Code       │
│   □  CODEX    OpenAI Codex CLI  │
│                                 │
│  > KONSOLE                      │
│   ■  CMD     □  POWERSHELL      │
│                                 │
│   □  ALS ADMINISTRATOR          │
│   □  OHNE RÜCKFRAGEN            │
│                                 │
│        [ABBRECHEN]  [ START ]   │
└─────────────────────────────────┘
```

Die zuletzt getroffene Wahl ist vorgemerkt und `START` ist der
Vorgabeknopf — **ein Druck auf Enter genügt also**, der Dialog kostet
keinen Klick. `Esc` bricht ab und startet nichts.

Danach öffnet sich eine Konsole mit dem Projektordner als
Arbeitsverzeichnis, und darin läuft der gewählte Agent. Der Befehl
lautet im Kern immer

```
cmd /K claude      bzw.      cmd /K codex
```

`/K` hält das Fenster offen, wenn der Agent beendet wird — Ausgaben und
Fehler bleiben also lesbar. Was im Ordner liegt, spielt keine Rolle:
eine `start.bat` oder ein `npm run dev` werden nicht mehr ausgeführt.

Gefragt wird auf jedem Weg gleich — Doppelklick, `F5`, der `START`-Knopf
und auch das Starten direkt nach `+ NEU`. Fehlt der gewählte Agent im
PATH, sagt das eine Meldung im Terminal-Look, statt eine Konsole mit
einem Windows-Fehler aufzumachen.

Darunter steht, welche Shell die Konsole stellt: `CMD` oder `POWERSHELL`.
Für den Agenten selbst ändert das kaum etwas — seine eigenen Werkzeuge
wählt er selbst. PowerShell lädt aber das eigene Profil (`$PROFILE`),
`cmd` nicht.

Die Wahl steht als `last_agent` und `last_shell` in der `config.json`. Das Häkchen bei
`ALS ADMINISTRATOR` dagegen nicht — es ist bei jedem Start wieder leer.
Gemerkt hieße, dass jeder spätere Start still einen UAC-Dialog aufmacht;
erhöhte Rechte sind eine Ausnahme und keine Einstellung.

Wie die Konsole dabei aussieht, entscheidet das Konsolen-Design unter
[Einstellungen](#einstellungen).

Die neue Konsole erbt die Umgebung des Launchers — bis auf die Marker
einer laufenden Claude-Sitzung (`CLAUDE_CODE_CHILD_SESSION`,
`CLAUDE_CODE_SESSION_ID` und die übrigen aus `runner.SESSION_MARKERS`).
Wird ProjectHQ selbst einmal aus einer Claude-Sitzung heraus gestartet,
erbt er sie nämlich, und das Claude in der neuen Konsole hielte sich für
eine Unter-Sitzung und schriebe kein Transcript mehr. Die Liste ist
namentlich und kein `CLAUDE*`-Kahlschlag: eigene dauerhafte Einstellungen
wie `ANTHROPIC_API_KEY` erreichen die Konsole weiterhin.

Die Spalte `TYP` zeigt weiterhin, worum es sich handelt (`py`, `node`,
`bat`, `docker`, `web`, `dotnet`, `docs`, oder `-` für alles andere).
Das ist reine Information und beeinflusst den Start nicht.

## Ohne Rückfragen

Das Häkchen `OHNE RÜCKFRAGEN` hängt an den gewählten Agenten die Schalter,
mit denen er nicht mehr nachfragt (`runner.FREE_FLAGS`):

| Agent | Schalter |
|-------|----------|
| Claude | `--dangerously-skip-permissions` |
| Codex | `--sandbox danger-full-access --ask-for-approval never` |

Claude fragt dann vor keiner Dateiänderung und keinem Befehl mehr nach;
Codex läuft zusätzlich ohne seine Sandbox. Das Häkchen nennt die
Schalter des gerade gewählten Agenten, damit man sieht, was man erlaubt.

Das Häkchen hängt nicht an der Shell: es wirkt in `cmd` wie in
PowerShell. In PowerShell hält `-NoExit` das Fenster offen wie `/K` bei
`cmd`, und im CRT-Design färbt sich die PowerShell mit einem eigenen
Vorspann (`runner.ps_crt_prolog`), weil der `cmd`-Vorspann an PowerShell
scheitert: dort ist das `&` nicht erlaubt.

Gemerkt wird es wie das Admin-Häkchen nicht — sonst liefe jeder spätere
Start still ohne Rückfragen. Als Administrator in PowerShell wechselt
die erhöhte Konsole per `Set-Location` in den Projektordner
(`_elevated_ps_params`). Ob Claude den Schalter in einer erhöhten Konsole
annimmt, ist noch nicht ausprobiert.

## Als Administrator

Mit gesetztem Häkchen fragt Windows vorher nach — dieselbe Konsole, nur
mit erhöhten Rechten. Der Befehl darin ändert sich nicht. Der Weg
dorthin schon: `subprocess.Popen` kann nicht erhöhen, weil der neue
Prozess das Token des alten erbt. Daran führt unter Windows nur
`ShellExecuteW` mit dem Verb `runas` vorbei, und das nimmt eine
Kommandozeile statt einer Liste. Gebaut wird sie in `_elevated_params`,
von Hand statt mit `list2cmdline`: das schützt Anführungszeichen im
Inneren mit einem Backslash, und den liest `cmd` nicht als Schutz,
sondern als Zeichen. Die äußere Klammer darf `cmd` dagegen abziehen —
bei mehr als zwei Anführungszeichen streicht es genau das erste und das
letzte und führt den Rest aus.

Wird der UAC-Dialog mit `Nein` beantwortet, sagt das eine Meldung im
Terminal-Look. Sonst täte der Knopf kommentarlos nichts.

Ein erhöhter Prozess hängt an der Rechteerhöhung von Windows und nicht
mehr an ProjectHQ als Elternprozess: seine Umgebung bekommt er nicht von
uns, das Aussieben der Sitzungsmarker weiter oben greift dort also
nicht. Sie werden deshalb in der Konsole selbst gelöscht — `set NAME=`
ohne Wert entfernt eine Variable. Ist keiner geerbt, was der Normalfall
ist, bleibt der Befehl unverändert.

Denselben Weg nimmt der Projektordner. `ShellExecuteW` bekommt ihn
übergeben, benutzt ihn beim Verb `runas` aber nicht: gestartet wird der
Prozess nicht von uns, sondern vom Dienst hinter der Rechteerhöhung, und
der setzt sein eigenes Verzeichnis. Gemessen landete jede erhöhte
Konsole in `C:\Windows\System32` — egal, welches Projekt gemeint war.
Der Wechsel steht deshalb im Befehl selbst, als erstes Glied der Kette:
`cd /d "<Projektordner>"`. `/d` wechselt Ordner und Laufwerk in einem,
die Projekte liegen auf `D:`. Erst danach kommt das Aufräumen der
Marker, damit es dort geschieht, wo anschließend gearbeitet wird.

Auch das Terminal ohne Agent gibt es mit Rechten: `Shift+F4`, oder
`Terminal hier (Administrator)` im Rechtsklick-Menü.

## Einstellungen

Das Zahnrad oben rechts im Kopf öffnet alles an einem Ort: das
Konsolen-Design, das Design der Oberfläche, die Sprache und den
Projektordner. Nichts davon wird angefasst, solange nicht `OK` gedrückt
ist.

**Konsolen-Design** bestimmt, wie das Fenster aussieht, das beim Starten
eines Projekts aufgeht — und ebenso das Terminal auf `F4`. Beide öffnen
dieselbe Konsole, nur läuft bei `F4` kein Agent darin:

| Design | Was passiert |
|--------|--------------|
| `CRT` (Vorgabe) | Die Konsole färbt sich in den Farben des Launchers: Hintergrund `#050b05`, Schrift `#33ff66` |
| `KLASSISCH` | Windows-Standardfarben, genau wie eine von Hand geöffnete Konsole |

Im CRT-Design steht vor dem Agenten ein kurzer Vorspann:

```
cmd /K echo <OSC 11 Hintergrund><OSC 10 Schrift>&cls&claude
```

Die Konsole färbt sich also selbst, über zwei ANSI-Sequenzen. An Windows
oder an den Einstellungen des Windows-Terminals ändert das nichts, und
eine Konsole, die die Sequenzen nicht versteht, gibt sie als Text aus —
das darauffolgende `cls` wischt ihn sofort wieder weg. Die Farben kommen
aus `projecthq/theme.py`: ändert sich dort das Grün, ändert sich die
Konsole mit.

Geöffnet wird immer `cmd`, nie Windows Terminal — auch wenn `wt`
installiert ist. `wt` parst die übergebene Kommandozeile selbst und kommt
mit den ESC-Sequenzen des Vorspanns nicht zurecht: ein schlichter Befehl
geht durch, eine `&`-Kette auch, der Vorspann nicht. `F4` öffnete im
CRT-Design deshalb überhaupt kein Fenster, bis das aufgefallen ist.

Nicht einstellbar ist die **Schriftart** der Konsole — dafür bräuchte es
ein eigenes Profil im Windows-Terminal. Und die Farben, die der Agent
selbst ausgibt, bleiben unverändert; nur Hintergrund und
Standard-Textfarbe werden grün.

**Sprache** stellt die Oberfläche um: Deutsch (Vorgabe), Englisch,
Bosnisch/Kroatisch/Serbisch, Türkisch oder Spanisch. Der Wechsel wirkt
sofort, ohne Neustart — Knöpfe, Spaltenköpfe, Menüs, Dialoge, Meldungen
und der Startbildschirm. Nicht übersetzt werden die Notiz `AUFGABEN.md`
und was die Agenten selbst ausgeben.

Die Texte stehen in `projecthq/i18n.py`. Der deutsche Text ist dort
zugleich der Schlüssel: `tr("Löschen")` liefert die Übersetzung, und
fehlt eine, erscheint Deutsch statt eines leeren Knopfes.
`tests/test_i18n.py` prüft, dass jede Sprache jeden Text kennt, dieselben
Platzhalter benutzt und die Spaltenköpfe in ihre Spalten passen. Eine
weitere Sprache entsteht, indem man ihr Kürzel in `LANGUAGES`, ihren
Namen in `LANGUAGE_LABELS` und je Text eine Übersetzung einträgt.

**Projektordner** ist derselbe Pfad, der früher hinter `PFAD ...` lag.
Ein neuer Ordner lädt die Liste sofort neu.

Alles landet in `config.json` und gilt beim nächsten Start weiter.

## Automatischer Shutdown

`⏻ SHUTDOWN` unten links plant, dass der Rechner nach einer wählbaren
Zeit herunterfährt: `15`, `30`, `60` oder `120` Minuten, oder eine
eigene Minutenzahl. Geplant wird über das Windows-Bordmittel
`shutdown /t` — der Countdown läuft deshalb auch weiter, wenn HQ
zwischendurch geschlossen wird, und ein neu gestartetes HQ zeigt ihn
danach wieder an.

Solange ein Shutdown läuft, ist der Knopf rot, und die Statuszeile
zeigt die verbleibende Zeit und die Uhrzeit, zu der ausgeschaltet
wird. Ein Klick auf den roten Knopf fragt nach, ob abgebrochen werden
soll.

## Neues Projekt

`+ NEU` oder `Strg+N` fragt nach einem Namen, legt den Ordner unter
`projects_root` an und startet ihn sofort — mit derselben Frage, womit.
Der Ordner bleibt leer; alles Weitere legt der Agent an. Ungültige oder
bereits vergebene Namen werden abgelehnt, bevor etwas entsteht.

## Aufgaben je Projekt

Die Spalte `NOTIZ` sagt, ob zu einem Projekt etwas notiert ist: `≡`
heißt ja, `·` heißt noch nichts. Ein **Klick auf das Zeichen** öffnet die
Notiz in Notepad — genauso `F6` und `Aufgaben öffnen` im
Rechtsklick-Menü. Ein Doppelklick auf diese eine Spalte startet das
Projekt **nicht**; überall sonst in der Zeile tut er es wie gewohnt.

Die Notiz ist eine gewöhnliche Datei namens `AUFGABEN.md` **im
Projektordner selbst**, nicht neben der Konfiguration. Damit wandert sie
beim Verschieben mit, ist im Explorer zu finden und kann ins Git.
Existiert sie noch nicht, wird sie beim ersten Öffnen angelegt — und
zwar **gefüllt**, nicht leer:

```markdown
# Aufgaben — HQ

## Stand vom 07.09.2026, 03:10

**Woran gearbeitet wurde**
- 07.09. 02:49 · Claude · Spalten für letzte Aufgaben und verwendetes Modell
- 06.09. 23:26 · Codex · Ladezeit der Startseite halbieren

**Letzte Commits**
- 81ea5fe Erhoehte Konsole startete in System32 statt im Projekt

**Nicht committet** — 9 geändert, 5 neu

**Zuletzt geändert**
- 07.09. 02:44 · projecthq/activity.py
```

Woher das kommt, steht unter [Woher HQ den Stand kennt](#woher-hq-den-stand-kennt).

Darunter ist die Datei Ihre: die nächste Aufgabe, offene Fragen, was
immer Sie wollen. Der Launcher liest den Inhalt nie; er sieht nur, ob
die Datei da ist. Eine vorhandene Datei wird beim Öffnen **nie**
angefasst — sonst wüchse sie bei jedem Blick hinein. Löschen der Datei
setzt die Spalte auf `·` zurück.

### Später einen frischen Stand nachtragen

Rechtsklick → **Stand einfügen** schreibt einen neuen Block direkt unter
die Überschrift, alles Bisherige rutscht nach unten. In Notepad steht
das Neueste damit ohne Scrollen da, und nichts von Ihnen geht verloren.
Die Datei wird so zu einem kleinen Verlauf des Projekts.

## Womit zuletzt gearbeitet wurde

Die Spalte `AGENT` zeigt je Projekt, womit darin zuletzt gearbeitet
wurde: `■ CLAUDE` oder `● CODEX`. Ein `–` heißt, dass sich dazu nichts
finden ließ.

Maßgeblich sind die **Sitzungsarchive**, nicht nur die Starts über HQ.
Eine Konsole, die Sie selbst aufgemacht haben, zählt also genauso — sonst
stünde bei einem Projekt, in dem Sie gerade tippen, ein Strich. Woher die
Archive kommen, steht unter
[Woher HQ den Stand kennt](#woher-hq-den-stand-kennt).

Was HQ selbst gestartet hat, füllt die Lücke: es steht in `config.json`
unter `project_agents` und gilt, solange das Archiv nichts weiß — etwa
wenn ein altes Transkript weggeräumt wurde. Gemerkt wird erst, wenn der
Start geglückt ist; schlägt er fehl, weil der Agent nicht im PATH liegt,
bleibt die Spalte wie sie war.

## Zwei Daten pro Projekt

Die Liste zeigt `ERSTELLT` und `BEARBEITET`. `ERSTELLT` ist der
Erstellungszeitpunkt des Ordners und bleibt beim Umbenennen erhalten.

`BEARBEITET` ist die **jüngste Änderung im ganzen Projekt** — nicht die
Änderungszeit des Ordners. Die taugt dafür nicht: Windows hebt sie nur
an, wenn direkt darin ein Eintrag dazukommt, wegfällt oder umbenannt
wird. Wer in einer Datei tippt, erst recht in einem Unterordner, rührt
sie nicht an.

Gemessen an `Webshop`: der Ordner sagte 02.08., die jüngste
Datei war vom 07.09. — 35 Tage daneben. Und weil die Liste standardmäßig
nach diesem Feld sortiert, stand das Projekt ganz unten, während darin
gearbeitet wurde.

Die eigene `AUFGABEN.md` zählt dabei **nicht** mit. Sonst schöbe schon
ein Blick in die Aufgaben das Projekt nach oben, und die Liste zeigte,
wohin HQ geschrieben hat statt wo Sie gearbeitet haben.

## Sortieren

Ein Klick auf eine Spaltenüberschrift sortiert danach: `PROJEKT`, `TYP`,
`AGENT`, `NOTIZ`, `ERSTELLT` oder `BEARBEITET`. Die aktive Spalte
leuchtet hell und zeigt
mit `▲` oder `▼`, in welche Richtung sortiert wird; ein weiterer Klick
auf dieselbe Spalte dreht die Richtung um.

Der erste Klick auf eine Datumsspalte beginnt beim jüngsten Eintrag, der
erste Klick auf `PROJEKT` oder `TYP` bei A. `AGENT` und `NOTIZ` beginnen
mit den Projekten, die einen Eintrag haben — aufsteigend stünden zuerst
die leeren, also gerade die, nach denen niemand sucht, wenn er die
Spalte anklickt. Gleiche Werte werden immer alphabetisch nach Namen
aufgelöst.

Die Wahl landet in `config.json` und gilt beim nächsten Start weiter.
Ohne Eintrag wird nach `BEARBEITET` absteigend sortiert, das zuletzt
bearbeitete Projekt steht dann oben.

## Nur ein Fenster

CODE/X HQ läuft nur einmal. Wird er ein zweites Mal gestartet — Klick
auf die Verknüpfung, während er schon offen ist —, holt dieser Start das
vorhandene Fenster nach vorn und beendet sich selbst. Auch aus der
Taskleiste zurück.

Das ist kein Selbstzweck: Zwei Launcher nebeneinander hätten je eine
eigene Kopie der `config.json` und schrieben beim Speichern die ganze
Datei. Wer zuletzt speichert, gewinnt — der andere verlöre Sortierung,
Projektordner oder Konsolen-Design.

Wer wissen will, wie es gemacht ist: `projecthq/ui/instance.py`. Ob
schon einer läuft, beantwortet ein benannter Mutex von Windows; das
Nach-vorn-Holen läuft über eine benannte Pipe von Qt. `QLocalServer`
allein genügt dafür nicht — eine Pipe erlaubt mehrere Server desselben
Namens, ein zweites `listen` gelingt also ebenfalls.

Das gilt auch für den Entwicklungsbetrieb: Läuft die `.exe`, holt
`py -3.12 main.py` deren Fenster nach vorn, statt ein zweites zu öffnen.

## Favoriten

`Strg+D` oder der Eintrag im Rechtsklick-Menü heftet das ausgewählte
Projekt oben an. Angeheftete Projekte stehen immer vor allen anderen,
gleich wonach sortiert wird, und tragen statt des Pfeils ein Sternchen:

```
 *  Tarkov            py        01.09.2026    06.09.2026
 ►  Spielwiese        node      28.08.2026    05.09.2026
```

Es ist bewusst ein `*` und kein `★`: Consolas enthält keinen Stern, und
die einspringende Ersatzschrift malt ihn 13 px breit statt 7 — die
Spalten einer Favoritenzeile standen dadurch versetzt. Siehe
[Zeichen auf dem Raster](#zeichen-auf-dem-raster).

Untereinander gilt dieselbe Sortierung wie unten — ein Klick auf
`PROJEKT` ordnet oben wie unten alphabetisch. Derselbe Griff löst die
Anheftung wieder.

Die Namen stehen in `config.json` unter `favorites` und überleben
Umbenennen und Neustart. Wird ein Projekt gelöscht, verschwindet auch
sein Eintrag.

## config.json

Liegt im Benutzerprofil:

```
%APPDATA%\ProjectHQ\config.json
```

Nicht neben der `.exe` — dort stünde sie in `dist\ProjectHQ`, und genau
diesen Ordner räumt PyInstaller bei jedem Build mit `--noconfirm` leer;
die Einstellungen wären also nach jedem Neubau weg. Eine Datei, die
noch am alten Platz liegt, wird beim ersten Start einmalig übernommen
(kopiert, nicht verschoben).

Inhalt:

```json
{
  "projects_root": "D:\\Projekte",
  "favorites": [],
  "sort_key": "mtime",
  "sort_desc": true,
  "console_style": "crt",
  "app_theme": "green",
  "language": "de",
  "last_agent": "claude",
  "last_shell": "cmd",
  "project_agents": {
    "Tarkov": "codex"
  }
}
```

`sort_key` ist eine der Spalten (`name`, `kind`, `agent`, `has_note`,
`created`, `mtime`),
`sort_desc` die Richtung. Steht dort etwas Unbekanntes, wird beides
übergangen und wieder nach `BEARBEITET` absteigend sortiert.

`console_style` ist `crt` oder `classic`; steht dort etwas anderes, wird
`crt` verwendet. `last_agent` ist `claude` oder `codex` und hält fest,
was im Startdialog zuletzt gewählt wurde; Unbekanntes fällt auf
`claude` zurück. `last_shell` ist ebenso `cmd` oder `powershell`.
`language` ist `de`, `en`, `bhs`, `tr` oder `es`; Unbekanntes fällt auf
`de` zurück.

`project_agents` ordnet jedem Projekt den Agenten zu, mit dem es zuletzt
lief. Ein Eintrag mit unbekanntem Agenten wird beim Laden verworfen — nur
dieser eine, nicht die ganze Tabelle; das Projekt zeigt dann ein `–`.

`projects_root`, `console_style`, `app_theme` und `language` lassen sich im Programm über
`EINSTELLUNGEN` umstellen. Ist die Datei defekt oder fehlt sie, startet
das Programm mit Vorgaben. Ein `commands`-Block aus einer früheren
Version wird beim Laden übergangen.

## Löschen

Löschen verschiebt den Projektordner in den **Windows-Papierkorb**, nie
endgültig. Vorher erscheint ein Bestätigungsdialog mit Name, Pfad und
Größe. Aus dem Papierkorb lässt sich alles wiederherstellen.

## Fensterrahmen

Alle Fenster laufen rahmenlos und bringen ihre Titelleiste selbst mit,
sonst saesse ueber dem Terminal-Look eine graue Windows-Leiste. Das gilt
auch fuer die Dialoge und die Boot-Sequenz; statt `QMessageBox` gibt es
deshalb eine eigene kleine Meldungsbox.

Die Windows-Gesten bleiben trotzdem erhalten, weil Verschieben und
Groessenaenderung ueber `startSystemMove` und `startSystemResize` laufen:

| Geste | Wirkung |
|-------|---------|
| Leiste ziehen | Fenster verschieben, an den Bildschirmrand andocken |
| Doppelklick auf die Leiste | maximieren und zurueck |
| Rand oder Ecke ziehen | Groesse aendern (6 px Greifzone) |
| `─` `□` `×` | minimieren, maximieren, schliessen |

Der Rahmen leuchtet gruen, solange das Fenster aktiv ist, und faellt
sonst auf das gedaempfte Gruen zurueck. Lehnt die Plattform die
System-Gesten ab - etwa unter der Offscreen-Plattform in den Tests -,
rechnet `frame.py` die Geometrie selbst aus, das Fenster bleibt also
bedienbar.

## Woher HQ den Stand kennt

Vier Quellen, jede in `projecthq/activity.py`. Was nichts hergibt, taucht
in der Notiz nicht auf — ein leerer Abschnitt wäre schlimmer als ein
fehlender.

| Quelle | Woher | Deckt ab |
|--------|-------|----------|
| Woran gearbeitet wurde | Sitzungen von Claude und Codex | 14 von 24 Projekten |
| Letzte Commits | `git log -5 --oneline` | 7 von 24 |
| Nicht committet | `git status --porcelain` | 7 von 24 |
| Zuletzt geändert | jüngste Dateien im Ordner | alle |

**Claude** legt seine Sitzungen unter `~/.claude/projects/<Pfad>/` ab und
vergibt jeder selbst einen Titel — *„Admin-Startoptionen"*. Das ist die
beste Zusammenfassung, die zu haben ist. Eine ganz frische Sitzung hat
noch keinen; dann steht dort die erste Frage.

**Codex** legt nach Datum ab, nicht nach Projekt. Zu welchem Ordner eine
Sitzung gehört, steht in ihrer ersten Zeile — deshalb wird auch nur die
gelesen, solange nicht klar ist, ob die Datei überhaupt gemeint ist.
Einen Titel vergibt Codex nicht, also steht dort die erste Frage.

Zugeordnet wird über das mitgeschriebene Arbeitsverzeichnis, nicht über
den Ordnernamen: aus `Mein Projekt` und `Mein-Projekt` würde derselbe
Name, und beide bekämen die Notiz des anderen.

### Was daran unsicher ist

**Das Format ist undokumentiert.** Codex hat sein Protokoll zwischen Mai
und September 2026 umgestellt; beide Formen liegen nebeneinander im
Archiv, und HQ liest beide. Ändert sich wieder etwas, fällt der
betroffene Abschnitt still weg — die Notiz geht trotzdem auf.

**Sitzungen verschwinden.** In `.claude/projects` stehen zu manchen
Projekten nur noch leere Ordner. Das ist ein rollierendes Fenster, kein
Archiv. Deshalb wird der Stand **in die Datei geschrieben** und nicht bei
jedem Öffnen neu berechnet: was einmal drinsteht, bleibt.

**In der Notiz stehen Ihre Eingaben.** Ausschnitte dessen, was Sie
Claude und Codex geschrieben haben. `AUFGABEN.md` steht deshalb in der
`.gitignore` von HQ. In anderen Projekten müssen Sie das selbst
entscheiden — HQ fasst fremde `.gitignore`-Dateien nicht an.

### Laufzeit

Gemessen über alle 24 Projekte: 2,6 s zusammen, 0,03 bis 0,57 s je
Projekt. Das läuft **nur** beim Anlegen einer Notiz und bei „Stand
einfügen" — nie beim Scannen der Liste, sonst stünde das Fenster bei
jedem Fensterwechsel still. Zusätzlich begrenzen Zeitbudgets die Suche,
wie bei `folder_size` im Löschen-Dialog.

## Zeichen auf dem Raster

Die Spalten der Liste stehen nicht in einer Tabelle, sondern in einer
Textzeile aus gleich breiten Zeichen. Das trägt, solange jedes Zeichen
genau eine Zeichenbreite misst — bei Consolas 13 px sind das 7 px.

Der Haken: **keines** der benutzten Symbole steckt in Consolas. Gemalt
werden sie von der Schrift, die Windows ersatzweise einspringen lässt,
und die hält sich nicht ans Raster. Gemessen:

| Breite | Zeichen |
|--------|---------|
| 7 px (richtig) | `►` `*` `≡` `·` `–` `●` `○` `■` `□` `▪` `▬` `▒` `─` |
| 8 px | `▶` `◆` `◇` `▤` `▣` |
| 13 px | `★` `☆` `✱` `✦` `☰` |

Ein zu breites Zeichen schiebt alle Spalten seiner Zeile nach rechts.
Genau das tat der ursprüngliche Stern `★` der Favoritenzeile, sechs Pixel
weit — und es fiel nicht auf, weil der Test nur Zeichen *zählte*, statt
zu *messen*.

Nachmessen lässt sich das nur mit einer echten Schriftdatenbank. Die
Testsuite läuft mit `QT_QPA_PLATFORM=offscreen` und bekommt dort für
jedes Zeichen dieselbe Breite gemeldet — sie kann es also nicht prüfen.
Dafür gibt es

```
py -3.12 tools/messe_zeichen.py
```

Das Werkzeug misst jedes benutzte Symbol an einer fertig gestylten Liste
und meldet Rückgabecode 1, wenn eines nicht passt. Die Testsuite hält nur
fest, dass kein Symbol an dieser Messung vorbei hereinkommt: erlaubt ist,
was in `GRID_MARKS` in `projecthq/ui/window.py` steht. Wer ein neues
Symbol nehmen will, misst es erst und trägt es dann dort ein.

## Symbol

`assets/projecthq.ico` ist das Symbol der `.exe` und zugleich das
Fenster- und Taskleistensymbol zur Laufzeit. Es enthaelt alle Groessen
von 16 bis 256 Pixel, damit Taskleiste und Explorer nicht selbst
herunterrechnen muessen.

Gezeichnet wird es nicht von Hand, sondern von

```
py -3.12 tools/make_icon.py
```

Das Skript rendert bei 1024 Pixeln und rechnet herunter. Wer das Motiv
aendern will, aendert das 16x16-Raster `SKULL` in `tools/make_icon.py`
und laesst das Skript einmal laufen; danach `build.ps1` fuer eine neue
`.exe`.

Windows merkt sich Symbole aggressiv. Zeigt der Explorer nach einem Build
noch das alte Bild, hilft `ie4uinit.exe -show` oder ein Neustart des
Explorers.

## Neu bauen

```
powershell -ExecutionPolicy Bypass -File build.ps1
```

Das Skript führt erst die Tests aus und bricht ab, wenn eines fehlschlägt.
Danach paketiert PyInstaller nach `dist\ProjectHQ\`. Der Build ist bewusst
onedir und nicht onefile: das startet in etwa einer Sekunde statt in vier,
weil nichts entpackt werden muss.

**ProjectHQ muss dabei geschlossen sein.** Eine laufende `.exe` sperrt
ihre DLLs, PyInstaller kann `dist\ProjectHQ` dann nicht ersetzen und
bricht mitten im Aufräumen ab — mit einem halb geleerten Ordner. Passiert
das, hilft:

```
Remove-Item -Recurse -Force build, dist
```

und ein erneuter Lauf. Sonst zieht die Analyse Reste des kaputten
Ordners in den nächsten Build.

Nur die Tests laufen lassen:

```
py -3.12 -m pytest -q
```

## Aufbau

```
assets/
  projecthq.ico Anwendungssymbol (Totenkopf im CRT-Look)
tools/
  make_icon.py  zeichnet das Symbol neu
  messe_zeichen.py  misst, ob die Symbole der Liste aufs Raster passen
projecthq/
  config.py     Einstellungen, config.json
  scanner.py    Projekte finden, Typ bestimmen, Zeitstempel lesen,
                sortieren
  activity.py   Stand eines Projekts: Sitzungen von Claude und Codex,
                Commits, zuletzt geänderte Dateien
  runner.py     Starten, Anlegen, Umbenennen, Löschen,
                Explorer/Terminal/VS Code, Notiz (AUFGABEN.md)
  theme.py      Farbpalette und Qt-Stylesheet
  i18n.py       Sprachen der Oberfläche, tr()
  ui/
    window.py     Hauptfenster
    dialogs.py    Neues Projekt, Umbenennen, Löschen, Einstellungen,
                  Startdialog (womit?)
    boot.py       Boot-Sequenz
    crt.py        Scanline- und Vignetten-Overlay
    frame.py      eigener Fensterrahmen samt Titelleiste
    appicon.py    Symbol fuer Fenster und Taskleiste
main.py
```

`config.py`, `scanner.py`, `activity.py` und `runner.py` enthalten kein Qt. Das ist
Absicht: die gesamte Logik ist damit ohne laufende Oberfläche testbar.
Die Tests unter `tests/` decken diese drei Module direkt ab, dazu kommen
Durchstichtests, die das echte Hauptfenster offscreen aufbauen.

## Lizenz

[MIT](LICENSE)
