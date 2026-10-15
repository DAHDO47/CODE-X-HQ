# CODE/X HQ

A launcher for your projects folder with a CRT terminal look.
It lists all projects, opens them in Claude or Codex, creates new ones,
renames them and deletes them.

**Languages:** [Deutsch](README.md) · English ·
[Bosanski / Hrvatski / Srpski](README.bhs.md) · [Türkçe](README.tr.md) ·
[Español](README.es.md)

The German README is the reference; this translation follows it.

## Starting

**Ready-made build:** download `CODE-X-HQ-windows-x64.zip` from
[Releases](https://github.com/DAHDO47/CODE-X-HQ/releases/latest), unpack it and run `ProjectHQ\ProjectHQ.exe` — no Python
needed. On first start pick your projects folder under **Settings**
(default: `%USERPROFILE%\Projekte`). `claude` or `codex` must be installed
and on the PATH.

When built from source, the `.exe` is here:

```
dist\ProjectHQ\ProjectHQ.exe
```

Pin the `.exe` to the taskbar or put a shortcut on the desktop. The boot
sequence can be skipped with a click or a key press;
`ProjectHQ.exe --no-boot` skips it permanently.

## Usage

Everything is reachable with the mouse: a double click starts a project,
a right click opens the menu with all actions, and the sidebar on the left
offers the same actions for the selected entry.

| Key | Action |
|-----|--------|
| Double click / F5 | Start project |
| Ctrl+N | Create new project |
| F2 | Rename |
| Del | Delete (to the recycle bin) |
| F4 | Terminal in the project folder |
| F6 | The project's tasks in Notepad |
| Shift+F4 | Terminal as administrator |
| Ctrl+D | Pin or unpin as favourite |
| Ctrl+R | Re-read the list, recompute date and agent |
| Ctrl+F | Jump to the search field |
| Esc | Clear the search, otherwise close |

The search filters live while typing, over name **and** type: `node` shows
all Node projects. A click on a column header sorts the list by it.

The list has six columns:

```
 ►  PROJECT           TYPE   AGENT      NOTE    CREATED      MODIFIED
 *  Tarkov            node   ■ CLAUDE     ≡     28.08.2026   05.09.2026
 ►  Webshop           py     ● CODEX      ≡     24.05.2026   02.08.2026
 ►  Homepage          web    –            ·     22.06.2026   27.07.2026
```

The list is re-read with `Ctrl+R` — and automatically whenever the window
comes back to the foreground. A folder created meanwhile in Explorer
therefore shows up right away. The selection is kept.

One difference between the two: computing `MODIFIED` and `AGENT` takes
about 320 ms for 24 projects — too much for every Alt-Tab. The automatic
scan therefore uses the remembered values (about 40 ms);
**`Ctrl+R` recomputes them**. A project HQ has never seen is always
computed, so a fresh folder shows the right date straight away.

## How a project starts

When starting, a dialog asks what to start with:

```
┌─ START WITH? ───────────────────┐
│  > PROJECT:  Tarkov             │
│                                 │
│   ■  CLAUDE   Claude Code       │
│   □  CODEX    OpenAI Codex CLI  │
│                                 │
│  > CONSOLE                      │
│   ■  CMD     □  POWERSHELL      │
│                                 │
│   □  AS ADMINISTRATOR           │
│   □  NO CONFIRMATIONS           │
│                                 │
│           [CANCEL]  [ START ]   │
└─────────────────────────────────┘
```

The last choice is preselected and `START` is the default button —
**pressing Enter is enough**, so the dialog costs no extra click. `Esc`
cancels and starts nothing.

Then a console opens with the project folder as its working directory,
and the chosen agent runs in it. At its core the command is always

```
cmd /K claude      or      cmd /K codex
```

`/K` keeps the window open when the agent exits — output and errors stay
readable. What lies in the folder does not matter: a `start.bat` or an
`npm run dev` is no longer executed.

Every path asks the same way — double click, `F5`, the `START` button and
also starting right after `+ NEW`. If the chosen agent is missing from the
PATH, a message in the terminal look says so instead of opening a console
with a Windows error.

Below that you choose which shell provides the console: `CMD` or
`POWERSHELL`. For the agent itself this hardly changes anything — it picks
its own tools. PowerShell does load your profile (`$PROFILE`), `cmd` does
not.

The choice is stored as `last_agent` and `last_shell` in `config.json`.
The `AS ADMINISTRATOR` tick is not — it is empty again at every start.
Remembering it would mean every later start silently opens a UAC dialog;
elevated rights are an exception, not a setting.

What the console looks like is decided by the console design under
[Settings](#settings).

The new console inherits the launcher's environment — except the markers
of a running Claude session (`CLAUDE_CODE_CHILD_SESSION`,
`CLAUDE_CODE_SESSION_ID` and the others in `runner.SESSION_MARKERS`). If
ProjectHQ itself is ever started from inside a Claude session, it
inherits them, and the Claude in the new console would take itself for a
sub-session and stop writing a transcript. The list is by name and not a
`CLAUDE*` sweep: your own permanent settings such as `ANTHROPIC_API_KEY`
still reach the console.

The `TYPE` column still shows what kind of project it is (`py`, `node`,
`bat`, `docker`, `web`, `dotnet`, `docs`, or `-` for anything else). This
is information only and does not affect the start.

## No confirmations

The `NO CONFIRMATIONS` tick appends the flags with which the chosen agent
stops asking (`runner.FREE_FLAGS`):

| Agent | Flags |
|-------|-------|
| Claude | `--dangerously-skip-permissions` |
| Codex | `--sandbox danger-full-access --ask-for-approval never` |

Claude then no longer asks before any file change or command; Codex
additionally runs without its sandbox. The tick names the flags of the
currently chosen agent, so you can see what you are allowing.

The tick does not depend on the shell: it works in `cmd` as well as in
PowerShell. In PowerShell `-NoExit` keeps the window open like `/K` does
in `cmd`, and in the CRT design PowerShell colours itself with its own
prologue (`runner.ps_crt_prolog`), because the `cmd` prologue fails in
PowerShell: `&` is not allowed there.

Like the admin tick it is not remembered — otherwise every later start
would silently run without confirmations. As administrator in PowerShell
the elevated console changes into the project folder with `Set-Location`
(`_elevated_ps_params`). Whether Claude accepts the flag in an elevated
console has not been tried yet.

## As administrator

With the tick set, Windows asks first — the same console, just with
elevated rights. The command inside does not change. The way there does:
`subprocess.Popen` cannot elevate because the new process inherits the
old one's token. On Windows the only way around that is `ShellExecuteW`
with the verb `runas`, and it takes a command line instead of a list. It
is built in `_elevated_params`, by hand rather than with `list2cmdline`:
that protects inner quotes with a backslash, and `cmd` reads the
backslash not as protection but as a character. The outer pair of quotes,
on the other hand, `cmd` may strip — with more than two quotes it removes
exactly the first and the last and runs the rest.

If the UAC dialog is answered with `No`, a message in the terminal look
says so. Otherwise the button would silently do nothing.

An elevated process hangs off Windows' elevation and no longer off
ProjectHQ as its parent: it does not get its environment from us, so the
filtering of session markers above does not apply there. They are
therefore deleted in the console itself — `set NAME=` without a value
removes a variable. If none was inherited, which is the normal case, the
command stays unchanged.

The project folder takes the same route. `ShellExecuteW` receives it but
does not use it with the verb `runas`: the process is started not by us
but by the service behind the elevation, and that sets its own directory.
Measured, every elevated console landed in `C:\Windows\System32` — no
matter which project was meant. The change of directory is therefore part
of the command itself, as the first link of the chain:
`cd /d "<project folder>"`. `/d` changes folder and drive in one go; the
projects live on `D:`. Only after that come the marker clean-ups, so they
happen where the work continues.

The terminal without an agent is also available with rights: `Shift+F4`,
or `Terminal here (administrator)` in the right-click menu.

## Settings

The gear at the top right opens everything in one place: the console
design, the interface design, the language and the projects folder.
Nothing is touched until `OK` is pressed.

The **console design** decides what the window looks like that opens
when a project starts — and likewise the terminal on `F4`. Both open the
same console; on `F4` no agent runs in it:

| Design | What happens |
|--------|--------------|
| `CRT` (default) | The console takes on the launcher's colours: background `#050b05`, text `#33ff66` |
| `CLASSIC` | Windows default colours, exactly like a console opened by hand |

In the CRT design a short prologue precedes the agent:

```
cmd /K echo <OSC 11 background><OSC 10 text>&cls&claude
```

So the console colours itself, using two ANSI sequences. This changes
nothing in Windows or in the Windows Terminal settings, and a console
that does not understand the sequences prints them as text — the
following `cls` wipes it away at once. The colours come from
`projecthq/theme.py`: if the green changes there, the console changes
with it.

It always opens `cmd`, never Windows Terminal — even if `wt` is
installed. `wt` parses the command line it is given itself and cannot
cope with the ESC sequences of the prologue: a plain command goes
through, an `&` chain too, the prologue does not. Until that was noticed,
`F4` opened no window at all in the CRT design.

The console **font** cannot be set — that would need a dedicated Windows
Terminal profile. And the colours the agent prints itself stay as they
are; only the background and the default text colour turn green.

**Language** switches the interface: German (default), English,
Bosnian/Croatian/Serbian, Turkish or Spanish. The switch takes effect
immediately, without a restart — buttons, column headers, menus, dialogs,
messages and the boot screen. Not translated are the note `AUFGABEN.md`
and whatever the agents print themselves.

The texts live in `projecthq/i18n.py`. The German text is also the key
there: `tr("Löschen")` returns the translation, and if one is missing,
German appears instead of an empty button. `tests/test_i18n.py` checks
that every language knows every text, uses the same placeholders and that
the column headers fit their columns. Another language is added by
entering its code in `LANGUAGES`, its name in `LANGUAGE_LABELS` and a
translation for each text.

The **projects folder** is the same path that used to sit behind
`PATH ...`. A new folder reloads the list right away.

Everything goes into `config.json` and still applies at the next start.

## Automatic shutdown

`⏻ SHUTDOWN` at the bottom left schedules the computer to shut down after
a chosen time: `15`, `30`, `60` or `120` minutes, or a custom number of
minutes. It is scheduled with the Windows tool `shutdown /t` — so the
countdown keeps running even if HQ is closed in between, and a newly
started HQ shows it again.

While a shutdown is pending the button is red, and the status line shows
the remaining time and the time at which the computer turns off. A click
on the red button asks whether to cancel.

## New project

`+ NEW` or `Ctrl+N` asks for a name, creates the folder under
`projects_root` and starts it right away — with the same question about
what to start with. The folder stays empty; the agent creates everything
else. Invalid or already taken names are rejected before anything is
created.

## Tasks per project

The `NOTE` column says whether anything is noted for a project: `≡` means
yes, `·` means nothing yet. A **click on the symbol** opens the note in
Notepad — as do `F6` and `Open tasks` in the right-click menu. A double
click on this one column does **not** start the project; anywhere else in
the row it does as usual.

The note is an ordinary file called `AUFGABEN.md` **in the project folder
itself**, not next to the configuration. So it moves with the project, can
be found in Explorer and can go into Git. If it does not exist yet, it is
created on first opening — and **filled**, not empty:

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

The note is written in German regardless of the interface language.
Where its content comes from is described under
[Where HQ gets the status from](#where-hq-gets-the-status-from).

Below that the file is yours: the next task, open questions, whatever you
like. The launcher never reads the content; it only sees whether the file
exists. An existing file is **never** touched when opened — otherwise it
would grow with every look. Deleting the file resets the column to `·`.

### Adding a fresh status later

Right click → **Insert status** writes a new block directly below the
heading; everything before moves down. In Notepad the newest is visible
without scrolling, and nothing of yours is lost. The file thus becomes a
small history of the project.

## What was used last

The `AGENT` column shows per project what was last used in it:
`■ CLAUDE` or `● CODEX`. A `–` means nothing could be found.

What counts are the **session archives**, not just starts through HQ. A
console you opened yourself counts just the same — otherwise a project you
are typing in right now would show a dash. Where the archives come from is
described under
[Where HQ gets the status from](#where-hq-gets-the-status-from).

What HQ started itself fills the gap: it is stored in `config.json` under
`project_agents` and applies as long as the archive knows nothing — for
example when an old transcript was cleared away. It is only remembered
once the start has succeeded; if it fails because the agent is not on the
PATH, the column stays as it was.

## Two dates per project

The list shows `CREATED` and `MODIFIED`. `CREATED` is the folder's
creation time and survives renaming.

`MODIFIED` is the **latest change anywhere in the project** — not the
folder's modification time. That one is no good for this: Windows only
raises it when an entry is added, removed or renamed directly inside.
Typing in a file, let alone in a subfolder, does not touch it.

Measured on `Webshop`: the folder said 02.08., the newest file
was from 07.09. — 35 days off. And because the list sorts by this field
by default, the project sat at the very bottom while it was being worked
on.

HQ's own `AUFGABEN.md` does **not** count. Otherwise a mere look at the
tasks would push the project up, and the list would show where HQ wrote
instead of where you worked.

## Sorting

A click on a column header sorts by it: `PROJECT`, `TYPE`, `AGENT`,
`NOTE`, `CREATED` or `MODIFIED`. The active column is bright and shows
with `▲` or `▼` which direction it sorts in; another click on the same
column reverses the direction.

The first click on a date column starts with the newest entry, the first
click on `PROJECT` or `TYPE` with A. `AGENT` and `NOTE` start with the
projects that have an entry — ascending would put the empty ones first,
exactly the ones nobody is looking for when clicking the column. Equal
values are always resolved alphabetically by name.

The choice goes into `config.json` and still applies at the next start.
Without an entry the list is sorted by `MODIFIED` descending, so the most
recently edited project is on top.

## Only one window

CODE/X HQ runs only once. If it is started a second time — a click on
the shortcut while it is already open — that start brings the existing
window to the front and exits itself. It also brings it back from the
taskbar.

This is not an end in itself: two launchers side by side would each hold
their own copy of `config.json` and write the whole file when saving.
Whoever saves last wins — the other would lose sorting, projects folder or
console design.

How it is done: `projecthq/ui/instance.py`. Whether one is already running
is answered by a named Windows mutex; bringing it to the front works over
a named Qt pipe. `QLocalServer` alone is not enough — a pipe allows
several servers with the same name, so a second `listen` succeeds as well.

This also applies during development: if the `.exe` is running,
`py -3.12 main.py` brings its window to the front instead of opening a
second one.

## Favourites

`Ctrl+D` or the entry in the right-click menu pins the selected project to
the top. Pinned projects always come before all others, whatever the sort
order, and carry an asterisk instead of the arrow:

```
 *  Tarkov            py        01.09.2026    06.09.2026
 ►  Spielwiese        node      28.08.2026    05.09.2026
```

It is deliberately a `*` and not a `★`: Consolas has no star, and the
fallback font draws it 13 px wide instead of 7 — the columns of a
favourite row were shifted as a result. See
[Characters on the grid](#characters-on-the-grid).

Among themselves the same sorting applies as below — a click on `PROJECT`
orders alphabetically at the top as well as below. The same shortcut
unpins again.

The names are stored in `config.json` under `favorites` and survive
renaming and restarts. When a project is deleted, its entry disappears
too.

## config.json

Lives in the user profile:

```
%APPDATA%\ProjectHQ\config.json
```

Not next to the `.exe` — it would be in `dist\ProjectHQ` there, and
PyInstaller empties exactly that folder with `--noconfirm` on every build;
the settings would be gone after every rebuild. A file still in the old
place is taken over once at the first start (copied, not moved).

Contents:

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

`sort_key` is one of the columns (`name`, `kind`, `agent`, `has_note`,
`created`, `mtime`), `sort_desc` the direction. If something unknown is in
there, both are skipped and the list is again sorted by `MODIFIED`
descending.

`console_style` is `crt` or `classic`; anything else falls back to `crt`.
`last_agent` is `claude` or `codex` and records what was last chosen in
the start dialog; anything unknown falls back to `claude`. `last_shell` is
likewise `cmd` or `powershell`. `language` is `de`, `en`, `bhs`, `tr` or
`es`; anything unknown falls back to `de`.

`project_agents` maps each project to the agent it last ran with. An
entry with an unknown agent is dropped on loading — only that one, not
the whole table; the project then shows a `–`.

`projects_root`, `console_style`, `app_theme` and `language` can be
changed in the program under `SETTINGS`. If the file is broken or
missing, the program starts with defaults. A `commands` block from an
earlier version is skipped on loading.

## Deleting

Deleting moves the project folder to the **Windows recycle bin**, never
permanently. Before that a confirmation dialog shows name, path and size.
Everything can be restored from the recycle bin.

## Window frame

All windows run frameless and bring their own title bar, otherwise a grey
Windows bar would sit above the terminal look. That also applies to the
dialogs and the boot sequence; instead of `QMessageBox` there is a small
message box of its own.

The Windows gestures still work, because moving and resizing go through
`startSystemMove` and `startSystemResize`:

| Gesture | Effect |
|---------|--------|
| Drag the bar | Move the window, snap to the screen edge |
| Double click the bar | Maximise and back |
| Drag an edge or corner | Resize (6 px grip zone) |
| `─` `□` `×` | Minimise, maximise, close |

The frame glows green while the window is active and falls back to the
dimmed green otherwise. If the platform refuses the system gestures — for
example under the offscreen platform in the tests — `frame.py` computes
the geometry itself, so the window stays usable.

## Where HQ gets the status from

Four sources, each in `projecthq/activity.py`. Whatever yields nothing
does not appear in the note — an empty section would be worse than a
missing one.

| Source | From | Covers |
|--------|------|--------|
| What was worked on | Claude and Codex sessions | 14 of 24 projects |
| Recent commits | `git log -5 --oneline` | 7 of 24 |
| Not committed | `git status --porcelain` | 7 of 24 |
| Recently changed | newest files in the folder | all |

**Claude** stores its sessions under `~/.claude/projects/<path>/` and
gives each one a title itself — *"Admin start options"*. That is the best
summary available. A brand-new session has none yet; then the first
question appears there.

**Codex** stores by date, not by project. Which folder a session belongs
to is in its first line — that is why only that line is read as long as
it is unclear whether the file is meant at all. Codex gives no title, so
the first question appears there.

The mapping uses the recorded working directory, not the folder name:
`My Project` and `My-Project` would become the same name, and each would
get the other's note.

### What is uncertain about it

**The format is undocumented.** Codex changed its log between May and
September 2026; both forms sit side by side in the archive, and HQ reads
both. If something changes again, the affected section silently drops out
— the note still opens.

**Sessions disappear.** In `.claude/projects` some projects only have
empty folders left. It is a rolling window, not an archive. That is why
the status is **written into the file** and not recomputed on every
opening: what is in there once stays.

**The note contains your input.** Excerpts of what you wrote to Claude and
Codex. `AUFGABEN.md` is therefore in HQ's `.gitignore`. In other projects
you have to decide that yourself — HQ does not touch other projects'
`.gitignore` files.

### Run time

Measured over all 24 projects: 2.6 s in total, 0.03 to 0.57 s per
project. This runs **only** when a note is created and on "Insert status"
— never while scanning the list, otherwise the window would freeze at
every window switch. In addition, time budgets limit the search, as with
`folder_size` in the delete dialog.

## Characters on the grid

The list's columns are not in a table but in a line of text made of
equally wide characters. That holds as long as every character is exactly
one character wide — with Consolas 13 px that is 7 px.

The catch: **none** of the symbols used is in Consolas. They are drawn by
the font Windows falls back to, and that one does not stick to the grid.
Measured:

| Width | Characters |
|-------|------------|
| 7 px (correct) | `►` `*` `≡` `·` `–` `●` `○` `■` `□` `▪` `▬` `▒` `─` |
| 8 px | `▶` `◆` `◇` `▤` `▣` |
| 13 px | `★` `☆` `✱` `✦` `☰` |

A character that is too wide pushes all columns of its row to the right.
That is exactly what the original star `★` of the favourite row did, six
pixels far — and it went unnoticed because the test only *counted*
characters instead of *measuring* them.

This can only be measured with a real font database. The test suite runs
with `QT_QPA_PLATFORM=offscreen` and gets the same width reported for
every character there — so it cannot check it. For that there is

```
py -3.12 tools/messe_zeichen.py
```

The tool measures every symbol used on a fully styled list and returns
exit code 1 if one does not fit. The test suite only makes sure no symbol
slips past this measurement: allowed is what is listed in `GRID_MARKS` in
`projecthq/ui/window.py`. Anyone who wants a new symbol measures it first
and then adds it there.

## Icon

`assets/projecthq.ico` is the icon of the `.exe` and also the window and
taskbar icon at runtime. It contains all sizes from 16 to 256 pixels, so
the taskbar and Explorer do not have to scale it down themselves.

It is not drawn by hand but by

```
py -3.12 tools/make_icon.py
```

The script renders at 1024 pixels and scales down. To change the motif,
change the 16x16 grid `SKULL` in `tools/make_icon.py` and run the script
once; then `build.ps1` for a new `.exe`.

Windows caches icons aggressively. If Explorer still shows the old image
after a build, `ie4uinit.exe -show` or restarting Explorer helps.

## Rebuilding

```
powershell -ExecutionPolicy Bypass -File build.ps1
```

The script first runs the tests and aborts if one fails. Then PyInstaller
packages into `dist\ProjectHQ\`. The build is deliberately onedir and not
onefile: it starts in about one second instead of four, because nothing
has to be unpacked.

**ProjectHQ must be closed while building.** A running `.exe` locks its
DLLs; PyInstaller then cannot replace `dist\ProjectHQ` and aborts in the
middle of cleaning up — leaving a half-emptied folder. If that happens,

```
Remove-Item -Recurse -Force build, dist
```

and another run help. Otherwise the analysis pulls remains of the broken
folder into the next build.

Running only the tests:

```
py -3.12 -m pytest -q
```

## Structure

```
assets/
  projecthq.ico application icon (skull in CRT look)
tools/
  make_icon.py  redraws the icon
  messe_zeichen.py  measures whether the list symbols fit the grid
projecthq/
  config.py     settings, config.json
  scanner.py    find projects, determine type, read timestamps,
                sort
  activity.py   status of a project: Claude and Codex sessions,
                commits, recently changed files
  runner.py     start, create, rename, delete,
                Explorer/Terminal/VS Code, note (AUFGABEN.md)
  theme.py      colour palette and Qt stylesheet
  i18n.py       interface languages, tr()
  ui/
    window.py     main window
    dialogs.py    new project, rename, delete, settings,
                  start dialog (with what?)
    boot.py       boot sequence
    crt.py        scanline and vignette overlay
    frame.py      custom window frame with title bar
    appicon.py    icon for window and taskbar
main.py
```

`config.py`, `scanner.py`, `activity.py` and `runner.py` contain no Qt.
That is intentional: all the logic can be tested without a running
interface. The tests under `tests/` cover these modules directly, plus
end-to-end tests that build the real main window offscreen.

## License

[MIT](LICENSE)
