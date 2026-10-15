"""Dialoge im Terminal-Look.

Auch die Dialoge tragen den eigenen Rahmen aus `frame`. Mit den Dialogen
von Qt ginge sonst mitten im Programm die Windows-Titelleiste wieder auf,
und genau die soll nirgends zu sehen sein - deshalb steht hier auch eine
eigene kleine Meldungsbox statt `QMessageBox`.
"""

from __future__ import annotations

from html import escape
from pathlib import Path
from typing import NamedTuple

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QButtonGroup,
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QRadioButton,
    QVBoxLayout,
    QWidget,
)

from .. import runner, theme
from ..config import (
    AGENT_LABELS,
    AGENT_NOTES,
    AGENTS,
    CONSOLE_STYLES,
    DEFAULT_AGENT,
    DEFAULT_CONSOLE_STYLE,
    DEFAULT_SHELL,
    SHELL_LABELS,
    SHELLS,
    Config,
    resolve_shell,
)
from ..i18n import LANGUAGE_LABELS, LANGUAGES, resolve_language, tr
from ..scanner import Project
from ..theme import DEFAULT_THEME, THEME_LABELS, THEMES
from .frame import wrap


class _ChromeDialog(QDialog):
    """Dialog ohne Systemrahmen, mit derselben Leiste wie das Hauptfenster.

    Der Inhalt kommt in `self.body`. Groesse aendern ist abgeschaltet:
    Dialoge sind so gross, wie ihr Inhalt sie macht.
    """

    def __init__(self, parent: QWidget, title: str) -> None:
        super().__init__(parent)
        self.setWindowTitle(title)

        content = QWidget()
        self.body = QVBoxLayout(content)
        self.body.setContentsMargins(18, 16, 18, 18)
        self.body.setSpacing(10)

        chrome = wrap(
            self, content, title, resizable=False, minimize=False, maximize=False
        )
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(chrome)


class _PromptDialog(_ChromeDialog):
    def __init__(self, parent: QWidget, title: str, hint: str, value: str) -> None:
        super().__init__(parent, title)
        self.setMinimumWidth(460)

        self.body.addWidget(QLabel(hint))
        self.field = QLineEdit(value)
        self.field.selectAll()
        self.body.addWidget(self.field)

        self.error = QLabel("")
        self.error.setStyleSheet(f"color: {theme.RED};")
        self.error.setWordWrap(True)
        self.body.addWidget(self.error)

        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel, parent=self
        )
        buttons.button(QDialogButtonBox.Ok).setText(tr("OK"))
        buttons.button(QDialogButtonBox.Cancel).setText(tr("ABBRECHEN"))
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        self.body.addWidget(buttons)

    def value(self) -> str:
        return self.field.text()

    def set_error(self, message: str) -> None:
        self.error.setText(message)


class _MessageDialog(_ChromeDialog):
    """Meldung mit einem oder zwei Knoepfen. Ersatz fuer `QMessageBox`."""

    def __init__(
        self,
        parent: QWidget,
        title: str,
        text: str,
        colour: str,
        accept_text: str,
        reject_text: str | None = None,
        *,
        danger: bool = False,
    ) -> None:
        super().__init__(parent, title)
        self.setMinimumWidth(460)

        label = QLabel(text)
        label.setTextFormat(Qt.RichText)
        label.setStyleSheet(f"color: {colour};")
        self.body.addWidget(label)

        row = QHBoxLayout()
        row.setSpacing(8)
        row.addStretch(1)
        if reject_text is not None:
            reject = QPushButton(reject_text)
            reject.clicked.connect(self.reject)
            row.addWidget(reject)
        accept = QPushButton(accept_text)
        if danger:
            accept.setObjectName("danger")
        accept.setDefault(True)
        accept.clicked.connect(self.accept)
        row.addWidget(accept)
        self.body.addLayout(row)


#: Was im Dialog neben dem jeweiligen Knopf steht.
CONSOLE_LABELS = {
    "crt": "CRT   GRÜN AUF SCHWARZ",
    "classic": "KLASSISCH   WINDOWS-STANDARD",
}

def _section(text: str) -> QLabel:
    label = QLabel(text)
    label.setStyleSheet(f"color: {theme.DIM};")
    return label


class StartChoice(NamedTuple):
    """Was im Startdialog gewaehlt wurde: womit - und mit welchen Rechten."""

    agent: str
    admin: bool
    #: Der Agent ohne Rueckfragen - Claude mit
    #: `--dangerously-skip-permissions`, Codex zudem ohne Sandbox.
    skip_permissions: bool = False
    #: `cmd` oder `powershell`: welche Shell die Konsole stellt.
    shell: str = DEFAULT_SHELL


class _AgentDialog(_ChromeDialog):
    """Womit soll dieses Projekt starten?

    Steht auf dem haeufigsten Weg des Programms - Doppelklick, F5, START -,
    darf also nicht bremsen: die zuletzt getroffene Wahl ist vorgemerkt und
    START ist der Vorgabeknopf. Ein Druck auf Enter genuegt damit.
    """

    def __init__(
        self,
        parent: QWidget | None,
        project: Project,
        last: str,
        last_shell: str = DEFAULT_SHELL,
    ) -> None:
        super().__init__(parent, tr("WOMIT STARTEN?"))
        self.setMinimumWidth(440)

        self.hint = QLabel(tr("> PROJEKT:  {name}", name=project.name))
        self.hint.setStyleSheet(f"color: {theme.DIM};")
        self.body.addWidget(self.hint)
        self.body.addSpacing(4)

        self.agent_buttons: dict[str, QRadioButton] = {}
        group = QButtonGroup(self)
        for agent in AGENTS:
            # Beschriftung und Zusatz kommen aus `config` - dort steht,
            # welche Agenten es gibt und wie sie heissen.
            button = QRadioButton(f"{AGENT_LABELS[agent]}   {AGENT_NOTES[agent]}")
            button.setChecked(agent == last)
            group.addButton(button)
            self.body.addWidget(button)
            self.agent_buttons[agent] = button
        # Steht in der Datei etwas Unbekanntes, waere sonst kein Knopf
        # gedrueckt und der Dialog haette nichts zurueckzugeben.
        if not any(b.isChecked() for b in self.agent_buttons.values()):
            self.agent_buttons[DEFAULT_AGENT].setChecked(True)

        # Die Shell wird gemerkt wie der Agent - sie aendert, worin er
        # laeuft, nicht, was er darf.
        self.body.addSpacing(6)
        self.body.addWidget(_section(tr("> KONSOLE")))
        self.shell_buttons: dict[str, QRadioButton] = {}
        shell_group = QButtonGroup(self)
        shell_row = QHBoxLayout()
        shell_row.setSpacing(16)
        for shell in SHELLS:
            button = QRadioButton(SHELL_LABELS[shell])
            button.setChecked(shell == resolve_shell(last_shell))
            shell_group.addButton(button)
            shell_row.addWidget(button)
            self.shell_buttons[shell] = button
        shell_row.addStretch(1)
        self.body.addLayout(shell_row)

        # Bewusst nicht gemerkt, anders als die Wahl des Agenten: ein
        # stehengebliebenes Haekchen hiesse, dass jeder spaetere Start
        # still einen UAC-Dialog aufmacht.
        self.body.addSpacing(6)
        self.admin_box = QCheckBox(tr("ALS ADMINISTRATOR"))
        self.body.addWidget(self.admin_box)

        # Aus demselben Grund nicht gemerkt, nur schwerer: ein
        # stehengebliebenes Haekchen hiesse, dass jeder spaetere Start
        # still ohne Rueckfragen laeuft. Die Beschriftung nennt die
        # Schalter des gewaehlten Agenten - man soll sehen, was man erlaubt.
        self.skip_box = QCheckBox()
        self.body.addWidget(self.skip_box)
        for button in self.agent_buttons.values():
            button.toggled.connect(self._sync_skip_box)
        self._sync_skip_box()

        self.body.addSpacing(6)
        row = QHBoxLayout()
        row.setSpacing(8)
        row.addStretch(1)
        cancel = QPushButton(tr("ABBRECHEN"))
        cancel.clicked.connect(self.reject)
        row.addWidget(cancel)
        self.start_button = QPushButton(tr("START"))
        self.start_button.setDefault(True)
        self.start_button.clicked.connect(self.accept)
        row.addWidget(self.start_button)
        self.body.addLayout(row)

    def selected_agent(self) -> str:
        return next(a for a, b in self.agent_buttons.items() if b.isChecked())

    def selected_shell(self) -> str:
        return next(s for s, b in self.shell_buttons.items() if b.isChecked())

    def _sync_skip_box(self) -> None:
        flags = runner.FREE_FLAGS[self.selected_agent()]
        self.skip_box.setText(tr("OHNE RÜCKFRAGEN   {flags}", flags=flags))

    def choice(self) -> StartChoice:
        return StartChoice(
            self.selected_agent(),
            self.admin_box.isChecked(),
            self.skip_box.isChecked(),
            self.selected_shell(),
        )


def ask_agent(
    parent: QWidget | None,
    project: Project,
    last: str,
    shell: str = DEFAULT_SHELL,
) -> StartChoice | None:
    """Fragt, womit gestartet wird. `None` heisst: abgebrochen, nichts tun."""
    dialog = _AgentDialog(parent, project, last, shell)
    if dialog.exec() != QDialog.Accepted:
        return None
    return dialog.choice()


class _SettingsDialog(_ChromeDialog):
    """Konsolen-Design, Design der Oberflaeche und Projektordner an einem Ort.

    Der Dialog fasst nichts an: er zeigt den Stand der `Config` und gibt
    ihn erst in `apply_to` zurueck. Abbrechen kostet damit nichts.
    """

    def __init__(self, parent: QWidget | None, config: Config) -> None:
        super().__init__(parent, tr("EINSTELLUNGEN"))
        self.setMinimumWidth(480)
        self._root = Path(config.projects_root)

        self.body.addWidget(_section(tr("> KONSOLE, IN DER EIN PROJEKT STARTET")))
        self.style_buttons: dict[str, QRadioButton] = {}
        group = QButtonGroup(self)
        for style in CONSOLE_STYLES:
            button = QRadioButton(tr(CONSOLE_LABELS[style]))
            button.setChecked(style == config.console_style)
            group.addButton(button)
            self.body.addWidget(button)
            self.style_buttons[style] = button
        # Steht in der Datei ein Design, das es nicht gibt, waere kein
        # Knopf gedrueckt und der Dialog haette nichts zurueckzugeben.
        if not any(b.isChecked() for b in self.style_buttons.values()):
            self.style_buttons[DEFAULT_CONSOLE_STYLE].setChecked(True)

        self.body.addSpacing(6)
        self.body.addWidget(_section(tr("> DESIGN DER OBERFLÄCHE")))
        self.theme_buttons: dict[str, QRadioButton] = {}
        theme_group = QButtonGroup(self)
        for name in THEMES:
            button = QRadioButton(tr(THEME_LABELS[name]))
            button.setChecked(name == config.app_theme)
            theme_group.addButton(button)
            self.body.addWidget(button)
            self.theme_buttons[name] = button
        # Dieselbe Regel wie beim Konsolen-Design: ein unbekanntes Design
        # in der Datei darf keinen Dialog ohne gedrueckten Knopf hinterlassen.
        if not any(b.isChecked() for b in self.theme_buttons.values()):
            self.theme_buttons[DEFAULT_THEME].setChecked(True)

        self.body.addSpacing(6)
        self.body.addWidget(_section(tr("> SPRACHE")))
        # Ein Dropdown statt Knoepfen: fuenf Sprachen untereinander
        # machten den Dialog doppelt so hoch.
        self.language_combo = QComboBox()
        for language in LANGUAGES:
            self.language_combo.addItem(LANGUAGE_LABELS[language], language)
        self.language_combo.setCurrentIndex(
            LANGUAGES.index(resolve_language(config.language))
        )
        self.body.addWidget(self.language_combo)

        self.body.addSpacing(6)
        self.body.addWidget(_section(tr("> PROJEKTORDNER")))
        row = QHBoxLayout()
        row.setSpacing(8)
        self.root_label = QLabel(str(self._root))
        row.addWidget(self.root_label, 1)
        change = QPushButton(tr("ÄNDERN ..."))
        change.clicked.connect(self.choose_root)
        row.addWidget(change)
        self.body.addLayout(row)

        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel, parent=self
        )
        buttons.button(QDialogButtonBox.Ok).setText(tr("OK"))
        buttons.button(QDialogButtonBox.Cancel).setText(tr("ABBRECHEN"))
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        self.body.addWidget(buttons)

    def selected_style(self) -> str:
        return next(s for s, b in self.style_buttons.items() if b.isChecked())

    def selected_theme(self) -> str:
        return next(t for t, b in self.theme_buttons.items() if b.isChecked())

    def selected_language(self) -> str:
        return self.language_combo.currentData()

    def selected_root(self) -> Path:
        return self._root

    def choose_root(self) -> None:
        chosen = QFileDialog.getExistingDirectory(
            self, tr("Projektordner wählen"), str(self._root)
        )
        if not chosen:
            return
        self._root = Path(chosen)
        self.root_label.setText(str(self._root))

    def apply_to(self, config: Config) -> bool:
        """Schreibt die Auswahl zurueck und meldet, ob sich etwas aenderte."""
        changed = False
        style = self.selected_style()
        if style != config.console_style:
            config.console_style = style
            changed = True
        chosen_theme = self.selected_theme()
        if chosen_theme != config.app_theme:
            config.app_theme = chosen_theme
            changed = True
        language = self.selected_language()
        if language != config.language:
            config.language = language
            changed = True
        if self._root != Path(config.projects_root):
            config.projects_root = self._root
            changed = True
        return changed


def open_settings(parent: QWidget, config: Config) -> bool:
    """Zeigt die Einstellungen. Gibt zurueck, ob sich etwas geaendert hat."""
    dialog = _SettingsDialog(parent, config)
    if dialog.exec() != QDialog.Accepted:
        return False
    return dialog.apply_to(config)


#: Feste Auswahl im Dropdown, in Minuten. Wer mehr oder etwas dazwischen
#: braucht, tippt es unter 'EIGENE EINGABE' ein.
SHUTDOWN_PRESETS_MINUTES = (15, 30, 60, 120)
CUSTOM_SHUTDOWN_ENTRY = "EIGENE EINGABE ..."


class _ShutdownDialog(_ChromeDialog):
    """Nach wie vielen Minuten der Rechner herunterfahren soll."""

    def __init__(self, parent: QWidget | None) -> None:
        super().__init__(parent, tr("AUTOMATISCHER SHUTDOWN"))
        self.setMinimumWidth(420)
        self._minutes = 0

        self.body.addWidget(_section(tr("> IN WIE VIELEN MINUTEN HERUNTERFAHREN?")))

        self.combo = QComboBox()
        for minutes in SHUTDOWN_PRESETS_MINUTES:
            self.combo.addItem(tr("{minutes} MINUTEN", minutes=minutes), minutes)
        self.combo.addItem(tr(CUSTOM_SHUTDOWN_ENTRY), None)
        self.combo.currentIndexChanged.connect(self._update_custom_field)
        self.body.addWidget(self.combo)

        self.custom_field = QLineEdit()
        self.custom_field.setPlaceholderText(tr("Minuten"))
        self.custom_field.setVisible(False)
        self.body.addWidget(self.custom_field)

        self.error = QLabel("")
        self.error.setStyleSheet(f"color: {theme.RED};")
        self.error.setWordWrap(True)
        self.body.addWidget(self.error)

        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel, parent=self
        )
        buttons.button(QDialogButtonBox.Ok).setText(tr("OK"))
        buttons.button(QDialogButtonBox.Cancel).setText(tr("ABBRECHEN"))
        buttons.accepted.connect(self._try_accept)
        buttons.rejected.connect(self.reject)
        self.body.addWidget(buttons)

    def _update_custom_field(self) -> None:
        self.custom_field.setVisible(self.combo.currentData() is None)

    def _try_accept(self) -> None:
        minutes = self.combo.currentData()
        if minutes is None:
            try:
                minutes = int(self.custom_field.text().strip())
            except ValueError:
                minutes = 0
            if minutes <= 0:
                self.error.setText(tr("Bitte eine positive Minutenzahl eingeben."))
                return
        self._minutes = minutes
        self.accept()

    def minutes(self) -> int:
        return self._minutes


def ask_shutdown_minutes(parent: QWidget | None) -> int | None:
    """Fragt, in wie vielen Minuten heruntergefahren wird. `None`: abgebrochen."""
    dialog = _ShutdownDialog(parent)
    if dialog.exec() == QDialog.Accepted:
        return dialog.minutes()
    return None


def confirm_cancel_shutdown(parent: QWidget, when: str) -> bool:
    """Ob ein laufender Shutdown wirklich abgebrochen werden soll."""
    dialog = _MessageDialog(
        parent,
        tr("SHUTDOWN ABBRECHEN"),
        "<pre>"
        + escape(tr("> Automatisches Herunterfahren um {when} Uhr", when=when))
        + "\n\n"
        + escape(tr("Wirklich abbrechen?"))
        + "</pre>",
        theme.AMBER,
        tr("JA, ABBRECHEN"),
        tr("NEIN"),
        danger=True,
    )
    return dialog.exec() == QDialog.Accepted


def ask_rename(parent: QWidget, project: Project) -> str | None:
    dialog = _PromptDialog(
        parent,
        tr("PROJEKT UMBENENNEN"),
        tr("> Neuer Name für '{name}':", name=project.name),
        project.name,
    )
    while dialog.exec() == QDialog.Accepted:
        try:
            runner.validate_name(dialog.value(), project.path.parent, project.path)
        except runner.RunnerError as exc:
            dialog.set_error(str(exc))
            continue
        return dialog.value().strip()
    return None


def ask_new_name(parent: QWidget) -> str | None:
    dialog = _PromptDialog(
        parent,
        tr("NEUES PROJEKT"),
        tr("> Name des neuen Projekts:"),
        "",
    )
    if dialog.exec() == QDialog.Accepted:
        return dialog.value()
    return None


def _fields(*rows: tuple[str, str]) -> str:
    """Beschriftete Zeilen fuer eine `<pre>`-Meldung, die Werte buendig.

    Die Spalte richtet sich nach der laengsten Beschriftung - die ist je
    Sprache verschieden lang, eine feste Zahl Leerzeichen passte nur fuer
    eine.
    """
    width = max(len(label) for label, _value in rows) + 3
    return "\n".join(
        escape(f"> {(label + ':').ljust(width)}{value}") for label, value in rows
    )


def confirm_delete(parent: QWidget, project: Project) -> bool:
    # Nur bis zum Budget gezaehlt: bei einem Projekt mit node_modules
    # stuende der Dialog sonst sekundenlang aus, und fuer die Frage, die er
    # stellt, genuegt eine Untergrenze.
    size = runner.size_label(project.path)
    dialog = _MessageDialog(
        parent,
        tr("LÖSCHEN BESTÄTIGEN"),
        "<pre>"
        + _fields(
            (tr("PROJEKT"), project.name),
            (tr("PFAD"), str(project.path)),
            (tr("GRÖSSE"), size),
        )
        + "\n\n"
        + escape(tr("In den Papierkorb verschieben?"))
        + "</pre>",
        theme.AMBER,
        tr("IN DEN PAPIERKORB"),
        tr("ABBRECHEN"),
        danger=True,
    )
    return dialog.exec() == QDialog.Accepted


def show_error(parent: QWidget, message: str) -> None:
    dialog = _MessageDialog(
        parent, tr("FEHLER"), f"<pre>&gt; {message}</pre>", theme.RED, tr("OK")
    )
    dialog.exec()
