"""Hauptfenster des Launchers."""

from __future__ import annotations

import time
from functools import partial
from pathlib import Path

from PySide6.QtCore import QEvent, QTimer, Qt, Signal
from PySide6.QtGui import (
    QAction,
    QColor,
    QFont,
    QFontMetrics,
    QKeySequence,
    QShortcut,
)
from PySide6.QtWidgets import (
    QApplication,
    QFrame,
    QGraphicsDropShadowEffect,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMenu,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from .. import activity, runner, theme
from .. import i18n
from ..config import AGENT_LABELS, AGENT_MARKS, Config
from ..i18n import tr
from ..scanner import SORT_STARTS_DESCENDING, Project, scan, sort_projects
from ..theme import LIST_BORDER, ROW_MARKER, ROW_PADDING, stylesheet
from . import dialogs
from .crt import CRTOverlay
from .frame import wrap

TITLE = "C O D E / X   H Q"

# Sortierschluessel, Ueberschrift und Breite in Zeichen. Die einzige
# Stelle, an der die Breiten stehen: `_make_item` baut die Zeilen daraus,
# `_size_columns` den Kopf. Die letzte Spalte bekommt mit 0 den Rest.
COLUMNS = (
    ("name", "PROJEKT", 32),
    ("kind", "TYP", 7),
    ("agent", "AGENT", 11),
    ("has_note", "NOTIZ", 8),
    ("created", "ERSTELLT", 14),
    ("mtime", "BEARBEITET", 0),
)

# Steht am Anfang jeder Listenzeile. Der Spaltenkopf ruecken denselben
# Betrag ein, damit die Ueberschriften ueber ihren Spalten stehen.
ROW_PREFIX = " ►  "

# Dasselbe fuer ein angeheftetes Projekt.
#
# Es muss nicht nur gleich viele Zeichen haben, sondern gleich breit
# *malen*. Der frueher benutzte Stern (U+2605) tat das nicht: Consolas
# hat ihn gar nicht, und die einspringende Ersatzschrift malte ihn 13 px
# breit statt 7 - die Spalten einer Favoritenzeile standen dadurch 5 px
# neben denen der uebrigen. Gemessen wurden alle Sterne der Schrift so;
# ein Zeichen auf voller Breite gibt es nicht, deshalb steht hier das
# schlichte Sternchen. `tests/test_window.py` misst jedes Zeichen der
# Liste nach.
FAVORITE_PREFIX = " *  "

#: Die Notizspalte. Drei Striche stehen fuer die Zeilen auf dem Blatt,
#: der Punkt fuer ein Projekt, zu dem noch nichts notiert ist. Auch sie
#: muessen genau eine Zeichenbreite messen.
NOTE_MARK = "≡"
NO_NOTE_MARK = "·"

#: Was in der Agentenspalte steht, solange ein Projekt nie ueber HQ
#: gestartet wurde.
NO_AGENT_MARK = "–"

#: Zeichen, die in der Liste stehen duerfen.
#:
#: Die Spalten stehen auf einem Raster aus gleich breiten Zeichen. Keines
#: dieser Symbole ist in Consolas enthalten - gemalt werden sie von der
#: einspringenden Ersatzschrift, und die haelt sich nicht ans Raster. Auf
#: Consolas 13 px (Grundbreite 7 px) gemessen:
#:
#:     7 px:  ► * ≡ · – ● ○ ■ □ ▪ ▬ ▒ ─
#:     8 px:  ▶ ◆ ◇ ▤ ▣
#:    13 px:  ★ ☆ ✱ ✦ ☰
#:
#: Ein zu breites Zeichen schiebt alle Spalten seiner Zeile nach rechts.
#: Genau das tat der frueher benutzte Stern ★, sechs Pixel weit, und es
#: fiel nicht auf, weil der Test nur Zeichen zaehlte statt zu messen.
#:
#: Nachmessen laesst sich das nur mit einer echten Schriftdatenbank -
#: unter `QT_QPA_PLATFORM=offscreen`, wie die Tests laufen, meldet Qt fuer
#: jedes Zeichen dieselbe Breite. Dafuer gibt es `tools/messe_zeichen.py`;
#: die Testsuite haelt hier nur fest, was dabei herauskam.
GRID_MARKS = frozenset("►*≡·–●○■□▪▬▒─ ")

LIST_FONT = ("Consolas", 11)


def fit(value: str, width: int) -> str:
    """Bringt `value` auf genau `width` Zeichen.

    Kuerzeres wird aufgefuellt, laengeres abgeschnitten - das letzte
    Zeichen ist dann ein '…', damit die Kuerzung zu sehen ist. Breite 0
    heisst: die letzte Spalte, sie bekommt den Rest und bleibt, wie sie ist.

    Das letzte Zeichen der Spalte bleibt immer frei. Sonst stiesse ein
    Wert, der sie genau ausfuellt, ohne Luecke an die naechste Spalte.
    """
    if not width:
        return value
    limit = width - 1
    if len(value) > limit:
        value = value[: limit - 1] + "…"
    return value.ljust(width)


class ColumnHeader(QLabel):
    """Anklickbare Spaltenueberschrift."""

    clicked = Signal()

    def __init__(self, text: str) -> None:
        super().__init__(text)
        self.setCursor(Qt.PointingHandCursor)

    def mousePressEvent(self, event) -> None:  # noqa: N802 (Qt-Namensschema)
        if event.button() == Qt.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)


class ProjectList(QListWidget):
    """Liste, die zu einem Klick auch sagt, wo er hinging.

    `itemClicked` reicht die Zeile durch, aber nicht die Stelle darin -
    und genau die entscheidet, ob der Klick der Notizspalte galt. Ein
    eigener Signaltyp ist billiger als ein Ereignisfilter am Viewport und
    laesst sich ohne Maus pruefen.
    """

    #: (Zeile, x im Listeninhalt)
    cell_clicked = Signal(object, int)
    cell_double_clicked = Signal(object, int)

    def mousePressEvent(self, event) -> None:  # noqa: N802 (Qt-Namensschema)
        super().mousePressEvent(event)
        self._report(self.cell_clicked, event)

    def mouseDoubleClickEvent(self, event) -> None:  # noqa: N802 (Qt-Namensschema)
        super().mouseDoubleClickEvent(event)
        self._report(self.cell_double_clicked, event)

    def _report(self, signal: Signal, event) -> None:
        """Meldet Zeile und Stelle, sofern der Klick eine Zeile getroffen hat."""
        if event.button() != Qt.LeftButton:
            return
        position = event.position().toPoint()
        item = self.itemAt(position)
        if item is not None:
            signal.emit(item, position.x())


class MainWindow(QMainWindow):
    def __init__(self, config: Config, config_path: Path) -> None:
        super().__init__()
        self.config = config
        self.config_path = config_path
        self.projects: list[Project] = []
        # Juengste Aenderung und zuletzt benutzter Agent kosten zusammen
        # rund 300 ms fuer 24 Projekte - zu viel fuer jeden
        # Fensterwechsel. Gerechnet wird beim Start und bei Strg+R.
        self.snapshot = activity.Snapshot()
        # Vor dem Aufbau gesetzt: resizeEvent kann feuern, bevor die
        # Bedienelemente existieren.
        self.overlay: CRTOverlay | None = None
        self._header_text = ""
        self._status_text = ""
        # Zaehlt waehrend eines geplanten Shutdowns jede Sekunde herunter.
        # Ruht ohne geplanten Shutdown - siehe `_sync_shutdown_ui`.
        self._shutdown_timer = QTimer(self)
        self._shutdown_timer.timeout.connect(self._on_shutdown_tick)

        self.setWindowTitle("CODE/X HQ")
        self.resize(980, 680)
        self.setStyleSheet(stylesheet())

        content = QWidget()
        outer = QVBoxLayout(content)
        # Schmaler als frueher: die 6 px Griffrand des eigenen Rahmens
        # kommen aussen dazu.
        outer.setContentsMargins(10, 10, 10, 10)
        outer.setSpacing(10)

        outer.addWidget(self._build_header())
        outer.addWidget(self._build_body(), 1)
        outer.addWidget(self._build_bottom_bar())

        self._size_columns()

        # Eigener Rahmen statt der Titelleiste von Windows.
        self.chrome = wrap(self, content, "CODE/X HQ")
        self.setCentralWidget(self.chrome)

        # Die Scanlines liegen ueber allem, auch ueber der eigenen Leiste.
        self.overlay = CRTOverlay(self.chrome)
        self.overlay.resize_to_parent()

        self._install_shortcuts()
        self._sync_shutdown_ui()
        self.refresh()

    # --- Aufbau ---------------------------------------------------------

    def _build_header(self) -> QWidget:
        frame = QFrame()
        frame.setObjectName("panel")
        outer = QVBoxLayout(frame)
        outer.setContentsMargins(14, 12, 14, 12)
        outer.setSpacing(2)

        self.title_label = QLabel(f"▓▒░ {TITLE} ░▒▓")
        title = self.title_label
        title.setObjectName("title")
        title.setAlignment(Qt.AlignCenter)
        title.setGraphicsEffect(self._phosphor_glow(22))

        self.subtitle = QLabel("")
        self.subtitle.setObjectName("subtitle")
        self.subtitle.setAlignment(Qt.AlignCenter)
        self.subtitle.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Preferred)

        titles = QVBoxLayout()
        titles.setSpacing(2)
        titles.addWidget(title)
        titles.addWidget(self.subtitle)

        # Das Zahnrad steht rechts oben, der Titel bleibt trotzdem mittig:
        # links ein Platzhalter in genau der Breite des Knopfes, damit
        # beide Seiten gleich viel freien Raum abbekommen.
        gear_size = 22
        placeholder = QWidget()
        placeholder.setFixedSize(gear_size, gear_size)

        self.settings_button = QPushButton("⚙")
        self.settings_button.setObjectName("gear")
        self.settings_button.setFixedSize(gear_size, gear_size)
        self.settings_button.setToolTip(tr("Einstellungen"))
        self.settings_button.clicked.connect(self._open_settings)

        row = QHBoxLayout()
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(0)
        row.addWidget(placeholder)
        row.addStretch(1)
        row.addLayout(titles)
        row.addStretch(1)
        row.addWidget(self.settings_button, 0, Qt.AlignTop)
        outer.addLayout(row)
        return frame

    def _phosphor_glow(self, radius: int) -> QGraphicsDropShadowEffect:
        """Weicher Schein in Phosphorgrün, wie er auf einer Röhre entsteht."""
        glow = QGraphicsDropShadowEffect(self)
        glow.setBlurRadius(radius)
        glow.setOffset(0, 0)
        glow.setColor(QColor(theme.GREEN))
        return glow

    def _build_search(self) -> QWidget:
        row = QWidget()
        layout = QHBoxLayout(row)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        self.search_prompt = QLabel(">")
        self.search_prompt.setStyleSheet(f"color: {theme.GREEN}; font-weight: bold;")
        layout.addWidget(self.search_prompt)

        self.search = QLineEdit()
        self.search.setPlaceholderText(tr("suchen ..."))
        self.search.textChanged.connect(self._apply_filter)
        layout.addWidget(self.search, 1)
        return row

    def _build_columns(self) -> QWidget:
        """Spaltenkopf. Gleiche Schrift und gleicher Einzug wie die Zeilen,
        sonst stehen die Ueberschriften neben ihren Spalten. Jede Spalte
        laesst sich anklicken und sortiert danach."""
        self.columns = QWidget()
        self.columns.setObjectName("columns")
        layout = QHBoxLayout(self.columns)
        # Linker Einzug wie bei einer Listenzeile: Rahmen der Liste, der
        # linke Rand der Zeile und ihr Innenabstand. Die Zahlen kommen aus
        # `theme`, damit Kopf und Zeilen nicht auseinanderlaufen koennen.
        layout.setContentsMargins(LIST_BORDER + ROW_MARKER + ROW_PADDING, 0, 0, 0)
        layout.setSpacing(0)

        # Breite bleibt offen: sie steht erst fest, wenn das Stylesheet
        # angewandt ist (siehe _size_columns).
        self._column_spacer = QWidget()
        layout.addWidget(self._column_spacer)

        self.column_labels: dict[str, ColumnHeader] = {}
        for key, title, _width in COLUMNS:
            label = ColumnHeader(tr(title))
            label.setFont(QFont(*LIST_FONT))
            label.clicked.connect(partial(self._sort_by, key))
            self.column_labels[key] = label
            layout.addWidget(label)

        layout.addStretch(1)
        self._update_column_marks()
        return self.columns

    def _size_columns(self) -> None:
        """Spaltenbreiten aus der Schrift, in der die Liste wirklich malt.

        Das Stylesheet setzt eine Schriftgroesse und uebergeht damit
        `setFont`. Nur die Metrik des fertig gestylten Listenfeldes passt
        deshalb zu den Zeichenbreiten der Zeilen; mit der Metrik von
        `QFont(*LIST_FONT)` stuende der Kopf ein Zeichen zu weit rechts.
        """
        self.list.ensurePolished()
        metrics = self.list.fontMetrics()
        self._column_spacer.setFixedWidth(metrics.horizontalAdvance(ROW_PREFIX))
        for key, _title, width in COLUMNS:
            if width:
                self.column_labels[key].setFixedWidth(
                    metrics.horizontalAdvance("0" * width)
                )

    def _update_column_marks(self) -> None:
        """Hebt die sortierte Spalte hervor und zeigt die Richtung an."""
        for key, title, _width in COLUMNS:
            active = key == self.config.sort_key
            arrow = ("▼" if self.config.sort_desc else "▲") if active else ""
            label = self.column_labels[key]
            title = tr(title)
            label.setText(f"{title} {arrow}" if arrow else title)
            label.setStyleSheet(f"color: {theme.GREEN if active else theme.DIM};")

    def _sort_by(self, key: str) -> None:
        """Ein Klick auf die aktive Spalte dreht die Richtung, sonst wird
        nach der neuen Spalte sortiert. Die Wahl bleibt bis zum naechsten
        Start erhalten."""
        if key == self.config.sort_key:
            self.config.sort_desc = not self.config.sort_desc
        else:
            self.config.sort_key = key
            self.config.sort_desc = SORT_STARTS_DESCENDING.get(key, False)
        self.config.save(self.config_path)
        self._update_column_marks()
        selected = self._selected()
        self.refresh(select_name=selected.name if selected else None)

    def _build_list(self) -> QWidget:
        self.list = ProjectList()
        self.list.setFont(QFont(*LIST_FONT))
        # Der Doppelklick laeuft ueber `cell_double_clicked` und nicht
        # ueber `itemDoubleClicked`: nur so ist zu sehen, ob er der
        # Notizspalte galt.
        self.list.cell_clicked.connect(self._on_cell_clicked)
        self.list.cell_double_clicked.connect(self._on_cell_double_clicked)
        self.list.itemSelectionChanged.connect(self._update_status)
        self.list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.list.customContextMenuRequested.connect(self._show_menu)
        return self.list

    def _build_status(self) -> QWidget:
        self.status = QLabel("")
        self.status.setObjectName("status")
        self.status.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Preferred)
        self._status_text = ""
        return self.status

    #: Die Arbeits-Aktionen im Seitenmenue, von oben nach unten.
    SIDEBAR_ACTIONS = (
        ("▶ START  F5", "_start"),
        ("+ NEU  Strg+N", "_new_project"),
        ("UMBENENNEN  F2", "_rename"),
        ("ORDNER", "_open_explorer"),
        ("TERMINAL  F4", "_open_terminal"),
        ("VS CODE", "_open_vscode"),
    )

    def _build_body(self) -> QWidget:
        """Seitenmenue links, Suche/Liste rechts daneben."""
        row = QWidget()
        layout = QHBoxLayout(row)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        layout.addWidget(self._build_sidebar())
        layout.addWidget(self._build_right(), 1)
        return row

    def _build_sidebar(self) -> QWidget:
        frame = QFrame()
        frame.setObjectName("sidebar")
        frame.setFixedWidth(190)
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.sidebar_buttons: list[QPushButton] = []
        for text, slot_name in self.SIDEBAR_ACTIONS:
            button = QPushButton(tr(text))
            self.sidebar_buttons.append(button)
            button.setObjectName("sidebarButton")
            button.clicked.connect(getattr(self, slot_name))
            layout.addWidget(button)
        layout.addStretch(1)
        return frame

    def _build_right(self) -> QWidget:
        column = QWidget()
        layout = QVBoxLayout(column)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        layout.addWidget(self._build_search())
        layout.addWidget(self._build_columns())
        layout.addWidget(self._build_list(), 1)
        layout.addWidget(self._build_status())
        return column

    def _build_bottom_bar(self) -> QWidget:
        """SHUTDOWN links, LÖSCHEN rechts - die beiden Sonderfaelle, getrennt
        vom Seitenmenue mit den taeglichen Aktionen."""
        row = QWidget()
        layout = QHBoxLayout(row)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        self.shutdown_button = QPushButton(tr("⏻ SHUTDOWN"))
        self.shutdown_button.clicked.connect(self._on_shutdown_clicked)
        layout.addWidget(self.shutdown_button)

        layout.addStretch(1)

        self.delete_button = QPushButton(tr("LÖSCHEN  ENTF"))
        self.delete_button.setObjectName("danger")
        self.delete_button.clicked.connect(self._delete)
        layout.addWidget(self.delete_button)
        return row

    def _install_shortcuts(self) -> None:
        for key, slot in (
            ("F5", self._start),
            ("Ctrl+N", self._new_project),
            ("F2", self._rename),
            ("F4", self._open_terminal),
            ("Shift+F4", self._open_terminal_admin),
            ("F6", self._open_note),
            # F5 startet ein Projekt, das Aktualisieren liegt deshalb auf
            # Strg+R. Und anders als der Scan beim Fensterwechsel erhebt
            # es Datum und Agent wirklich neu.
            ("Ctrl+R", self._reload),
            ("Ctrl+D", self._toggle_favorite),
            ("Delete", self._delete),
            ("Ctrl+F", self.search.setFocus),
            ("Escape", self._on_escape),
        ):
            QShortcut(QKeySequence(key), self, slot)

    # --- Daten ----------------------------------------------------------

    def refresh(self, select_name: str | None = None) -> None:
        found = scan(self.config.projects_root)
        # Zwei Dinge sieht der Scanner nicht und traegt das Fenster nach.
        # Beide vor dem Sortieren, damit sich danach sortieren laesst wie
        # nach jeder anderen Spalte auch.
        pfade = [p.path for p in found]
        for project in found:
            # Wann zuletzt etwas geschah. Die Ordnerzeit allein truegt:
            # sie merkt nichts davon, dass in einer Datei getippt wurde -
            # und ein ueber HQ gestartetes Projekt zaehlt schon deshalb,
            # weil es gestartet wurde, auch wenn dabei keine Datei angefasst
            # wurde. `max` statt Ersetzen: eine spaetere Dateiaenderung darf
            # den Start nicht unter sich begraben, und umgekehrt.
            geaendert = self.snapshot.changed(project.path) or project.mtime
            project.mtime = max(geaendert, self.config.started_of(project.name))
            # Womit gearbeitet wurde. Das Archiv gilt, weil es auch das
            # sieht, was nicht ueber HQ gestartet wurde; was HQ selbst
            # mitgeschrieben hat, fuellt die Luecke - etwa wenn ein altes
            # Transkript inzwischen weggeraeumt wurde.
            project.agent = self.snapshot.agent(
                project.path, pfade
            ) or self.config.agent_of(project.name)
        self.projects = sort_projects(
            found,
            self.config.sort_key,
            self.config.sort_desc,
            self.config.favorites,
        )
        self._apply_filter()
        if select_name:
            for index in range(self.list.count()):
                if self.list.item(index).data(Qt.UserRole) == select_name:
                    self.list.setCurrentRow(index)
                    break
        self._update_header()
        self._update_status()

    def present(self) -> None:
        """Holt das Fenster nach vorn, aus der Taskleiste notfalls zurueck.

        Ruft der zweite Start auf: statt eines weiteren Launchers soll der
        vorhandene erscheinen. `show` allein genuegte nicht - ein
        minimiertes Fenster bliebe minimiert.
        """
        if self.isMinimized():
            self.showNormal()
        self.show()
        self.raise_()
        self.activateWindow()

    def _rescan(self) -> None:
        """Den Ordner neu einlesen, ohne die Auswahl zu verlieren.

        Benutzt, was der Zwischenspeicher schon weiss. Laeuft bei jedem
        Fensterwechsel - neu zu rechnen kostete dort jedes Mal rund
        300 ms, und das ist bei Alt-Tab zu spueren.
        """
        selected = self._selected()
        self.refresh(select_name=selected.name if selected else None)

    def _reload(self) -> None:
        """Alles neu erheben - Strg+R.

        Eigene Methode und nicht ein Vorgabewert an `_rescan`: sonst
        raeumte der automatische Scan beim Fensterwechsel den
        Zwischenspeicher gleich mit ab, und das Sparen waere hinfaellig.
        """
        self.snapshot.clear()
        self._rescan()

    def _apply_filter(self) -> None:
        needle = self.search.text().strip().lower()
        self.list.clear()
        for project in self.projects:
            # Auch der Typ ist durchsuchbar: 'node' findet die
            # Node-Projekte, ohne dass man ihre Namen kennen muss.
            if needle and needle not in f"{project.name} {project.kind}".lower():
                continue
            self.list.addItem(self._make_item(project))
        if self.list.count() and self.list.currentRow() < 0:
            self.list.setCurrentRow(0)

    @staticmethod
    def _date(stamp: float) -> str:
        return time.strftime("%d.%m.%Y", time.localtime(stamp)) if stamp else "-"

    @staticmethod
    def _agent_cell(agent: str) -> str:
        """Symbol und Name des Agenten, oder ein Strich fuer 'noch nie'.

        Symbol *und* Name: das Symbol allein muesste man sich merken, und
        die Spalte hat Platz fuer beides.
        """
        if agent not in AGENT_MARKS:
            return NO_AGENT_MARK
        return f"{AGENT_MARKS[agent]} {AGENT_LABELS[agent]}"

    def _cells(self, project: Project) -> dict[str, str]:
        """Der Inhalt einer Zeile, je Spalte von `COLUMNS`."""
        return {
            "name": project.name,
            "kind": project.kind,
            "agent": self._agent_cell(project.agent),
            "has_note": NOTE_MARK if project.has_note else NO_NOTE_MARK,
            "created": self._date(project.created),
            "mtime": self._date(project.mtime),
        }

    def _make_item(self, project: Project) -> QListWidgetItem:
        prefix = (
            FAVORITE_PREFIX if self.config.is_favorite(project.name) else ROW_PREFIX
        )
        cells = self._cells(project)
        # Die Breiten stehen nur in COLUMNS - der Spaltenkopf rechnet mit
        # denselben Zahlen, sonst stuenden die Ueberschriften daneben.
        line = prefix + "".join(fit(cells[key], width) for key, _title, width in COLUMNS)

        item = QListWidgetItem(line)
        item.setData(Qt.UserRole, project.name)
        # Ein gekuerzter Name ist in der Zeile nicht mehr vollstaendig zu
        # lesen; der Mauszeiger zeigt den ganzen Pfad.
        item.setToolTip(str(project.path))
        return item

    def _column_at(self, x: int) -> str | None:
        """Welche Spalte an der Stelle `x` einer Listenzeile steht.

        `x` zaehlt im Inhalt der Liste, so wie ein Mausklick ihn liefert:
        ohne den Rahmen, aber mit dem linken Rand und dem Innenabstand
        einer Zeile. Gerechnet wird mit denselben Zahlen, aus denen
        `_size_columns` den Spaltenkopf einrueckt - sonst zeigte die
        Trefferzone woandershin als die Ueberschrift darueber.

        `None` heisst: links von der ersten Spalte, also auf dem Pfeil
        oder dem Stern. Dort gehoert der Klick keiner Spalte.
        """
        metrics = self.list.fontMetrics()
        step = metrics.horizontalAdvance("0")
        if step <= 0:  # theoretisch; eine Division durch 0 waere schlimmer
            return None
        offset = (
            x
            - ROW_MARKER
            - ROW_PADDING
            - metrics.horizontalAdvance(ROW_PREFIX)
        )
        if offset < 0:
            return None

        character = offset // step
        start = 0
        for key, _title, width in COLUMNS:
            # Breite 0 ist die letzte Spalte: ihr gehoert der ganze Rest.
            if not width or character < start + width:
                return key
            start += width
        return None

    def _project_of(self, item: QListWidgetItem) -> Project | None:
        """Das Projekt einer Zeile. Gemeint ist die angeklickte Zeile, nicht
        die ausgewaehlte: beim ersten Klick auf ein anderes Projekt waeren
        das zwei verschiedene."""
        return next(
            (p for p in self.projects if p.name == item.data(Qt.UserRole)), None
        )

    def _on_cell_clicked(self, item: QListWidgetItem, x: int) -> None:
        """Ein Klick in die Notizspalte oeffnet die Notiz."""
        if self._column_at(x) != "has_note":
            return
        project = self._project_of(item)
        if project is not None:
            self._open_note_of(project)

    def _on_cell_double_clicked(self, item: QListWidgetItem, x: int) -> None:
        """Doppelklick startet - ausser ueber der Notizspalte.

        Dort hat der erste Druck bereits die Notiz geoeffnet; ginge auch
        noch der Startdialog auf, taete eine Geste zweierlei. Wer auf das
        Symbol zielt, meint die Notiz.
        """
        if self._column_at(x) == "has_note":
            return
        project = self._project_of(item)
        if project is not None:
            self.list.setCurrentItem(item)
            self._start()

    def _selected(self) -> Project | None:
        item = self.list.currentItem()
        if item is None:
            return None
        name = item.data(Qt.UserRole)
        return next((p for p in self.projects if p.name == name), None)

    @staticmethod
    def _set_elided(label: QLabel, text: str) -> None:
        """Setzt den Text gekürzt, damit lange Pfade das Layout nicht dehnen."""
        metrics = QFontMetrics(label.font())
        width = max(label.width(), 120)
        label.setText(metrics.elidedText(text, Qt.ElideMiddle, width))

    def _update_header(self) -> None:
        root = self.config.projects_root
        if root.is_dir():
            count = tr("{count} PROJEKTE", count=len(self.projects))
            self._header_text = f"{root}   ·   {count}"
            self.subtitle.setStyleSheet(f"color: {theme.DIM};")
        else:
            missing = tr("ORDNER NICHT GEFUNDEN — 'EINSTELLUNGEN'")
            self._header_text = f"{root}   ·   {missing}"
            self.subtitle.setStyleSheet(f"color: {theme.AMBER};")
        self._set_elided(self.subtitle, self._header_text)

    def _update_status(self) -> None:
        """Zeigt den ausgewaehlten Pfad - oder, waehrend ein Shutdown laeuft,
        stattdessen den Countdown. Beide teilen sich dieselbe Zeile: der
        Shutdown ist die seltene Ausnahme und verdraengt den Pfad nur
        solange er aktiv ist."""
        if self.config.shutdown_at > time.time():
            self._status_text = self._shutdown_status_text()
            self.status.setStyleSheet(f"color: {theme.AMBER};")
        else:
            project = self._selected()
            self._status_text = (
                tr("> kein Projekt ausgewählt")
                if project is None
                else f"> {project.path}"
            )
            self.status.setStyleSheet(f"color: {theme.DIM};")
        self._set_elided(self.status, self._status_text)

    def _on_escape(self) -> None:
        if self.search.text():
            self.search.clear()
        else:
            self.close()

    # --- Aktionen -------------------------------------------------------

    def _guard(self) -> Project | None:
        project = self._selected()
        if project is None:
            dialogs.show_error(self, tr("Kein Projekt ausgewählt."))
        return project

    def _run(self, action) -> None:
        project = self._guard()
        if project is None:
            return
        try:
            action(project)
        except runner.RunnerError as exc:
            dialogs.show_error(self, str(exc))

    def _start(self) -> None:
        """Fragt, womit gestartet wird, und startet damit.

        Der Dialog sitzt hier und nicht an den Knoepfen: Doppelklick, F5
        und START laufen alle hier durch, also fragt jeder Weg gleich.
        Abbrechen startet nichts und aendert nichts.
        """
        project = self._guard()
        if project is None:
            return

        choice = dialogs.ask_agent(
            self, project, self.config.last_agent, shell=self.config.last_shell
        )
        if choice is None:
            return
        # Gemerkt werden nur Agent und Shell. Ein stehengebliebenes
        # Admin-Haekchen hiesse, dass jeder spaetere Start still einen
        # UAC-Dialog aufmacht.
        if (choice.agent, choice.shell) != (
            self.config.last_agent,
            self.config.last_shell,
        ):
            self.config.last_agent = choice.agent
            self.config.last_shell = choice.shell
            self.config.save(self.config_path)

        try:
            runner.start(
                project,
                choice.agent,
                self.config.console_style,
                choice.admin,
                skip_permissions=choice.skip_permissions,
                shell=choice.shell,
            )
        except runner.RunnerError as exc:
            dialogs.show_error(self, str(exc))
            return

        # Erst jetzt, nicht schon vor dem Start: in der Spalte soll nicht
        # stehen, womit nie gearbeitet wurde. Ein fehlender Agent faellt
        # genau hier auf - `runner.start` prueft den PATH.
        if self.config.agent_of(project.name) != choice.agent:
            self.config.remember_agent(project.name, choice.agent)
        # BEARBEITET zaehlt jeden Start mit, deshalb wird hier immer
        # gespeichert - anders als beim Agenten, der sich oft nicht aendert.
        self.config.remember_started(project.name, time.time())
        self.config.save(self.config_path)
        # Der eben gestartete Agent legt seine Sitzung sofort an. Das
        # Archiv gilt vor dem eigenen Vermerk, also wird es neu befragt -
        # nur das, nicht auch die Datumssuche.
        self.snapshot.forget_agents()
        self.refresh(select_name=project.name)

    def _new_project(self) -> None:
        """Legt einen Ordner an und oeffnet sofort Claude darin."""
        name = dialogs.ask_new_name(self)
        if name is None:
            return
        try:
            created = runner.create(self.config.projects_root, name)
        except runner.RunnerError as exc:
            dialogs.show_error(self, str(exc))
            return
        self.refresh(select_name=created.name)
        self._start()

    def _rename(self) -> None:
        project = self._guard()
        if project is None:
            return
        new_name = dialogs.ask_rename(self, project)
        if new_name is None:
            return
        try:
            runner.rename(project, new_name, self.config)
        except runner.RunnerError as exc:
            dialogs.show_error(self, str(exc))
            return
        self.config.save(self.config_path)
        self.refresh(select_name=new_name)

    def _delete(self) -> None:
        project = self._guard()
        if project is None:
            return
        if not dialogs.confirm_delete(self, project):
            return
        try:
            runner.delete(project, self.config)
        except runner.RunnerError as exc:
            dialogs.show_error(self, str(exc))
            return
        self.config.save(self.config_path)
        self.refresh()

    def _open_explorer(self) -> None:
        self._run(runner.open_explorer)

    def _open_terminal(self) -> None:
        self._run(
            lambda project: runner.open_terminal(project, self.config.console_style)
        )

    def _open_terminal_admin(self) -> None:
        """Dasselbe Terminal, nur mit Rechten - Shift+F4.

        Ein eigener Slot und kein Vorgabewert an `_open_terminal`: Qt
        reicht an einen Slot das `checked` des Knopfes durch, und das
        landete sonst als `admin` im Aufruf.
        """
        self._run(
            lambda project: runner.open_terminal(
                project, self.config.console_style, admin=True
            )
        )

    def _open_vscode(self) -> None:
        self._run(runner.open_vscode)

    def _open_note(self) -> None:
        """Die Notiz des ausgewaehlten Projekts - F6 und Rechtsklick."""
        project = self._guard()
        if project is not None:
            self._open_note_of(project)

    def _open_note_of(self, project: Project) -> None:
        """Oeffnet die Notiz und laesst die Liste es sofort sehen."""
        self._note_action(project, runner.open_note)

    def _insert_status(self) -> None:
        """Schreibt den aktuellen Stand oben in die Notiz und oeffnet sie.

        Anders als das blosse Oeffnen auch dann, wenn die Notiz schon da
        ist - so waechst sie zu einem kleinen Verlauf.
        """
        project = self._guard()
        if project is not None:
            self._note_action(project, runner.insert_status)

    def _note_action(self, project: Project, action) -> None:
        """Fuehrt `action` auf der Notiz aus und liest die Liste neu ein.

        Neu eingelesen wird, weil die Datei eben erst entstanden sein
        kann: ohne den Scan bliebe die Spalte bis zum naechsten
        Fensterwechsel bei ihrem Punkt stehen.
        """
        try:
            action(project)
        except runner.RunnerError as exc:
            dialogs.show_error(self, str(exc))
            return
        self.refresh(select_name=project.name)

    def _toggle_favorite(self) -> None:
        """Heftet das Projekt oben an die Liste oder loest es wieder.

        Die Sortierung darunter bleibt, wie sie ist: angeheftete Projekte
        stehen davor und untereinander in derselben Reihenfolge.
        """
        project = self._guard()
        if project is None:
            return
        self.config.toggle_favorite(project.name)
        self.config.save(self.config_path)
        self.refresh(select_name=project.name)

    def _open_settings(self) -> None:
        """Konsolen-Design, Design der Oberflaeche und Projektordner. Ohne
        Aenderung passiert nichts.

        Neu gescannt wird immer: welche Einstellung sich geaendert hat,
        weiss der Dialog, und ein Scan kostet nichts.
        """
        previous_theme = self.config.app_theme
        previous_language = self.config.language
        if not dialogs.open_settings(self, self.config):
            return
        self.config.save(self.config_path)
        if self.config.app_theme != previous_theme:
            self._apply_theme()
        if self.config.language != previous_language:
            self._apply_language()
        self.refresh()

    def _apply_language(self) -> None:
        """Schaltet die Sprache sofort um, ohne Neustart.

        Dialoge und das Rechtsklick-Menue entstehen bei jedem Oeffnen neu
        und sprechen damit von selbst die neue Sprache. Was dauerhaft
        steht - Knoepfe, Spaltenkopf, Suchfeld, Kopf- und Statuszeile -,
        bekommt hier seinen Text neu.
        """
        i18n.set_language(self.config.language)
        self.settings_button.setToolTip(tr("Einstellungen"))
        self.search.setPlaceholderText(tr("suchen ..."))
        for button, (text, _slot) in zip(self.sidebar_buttons, self.SIDEBAR_ACTIONS):
            button.setText(tr(text))
        self.shutdown_button.setText(tr("⏻ SHUTDOWN"))
        self.delete_button.setText(tr("LÖSCHEN  ENTF"))
        self._update_column_marks()
        self._update_header()
        self._update_status()

    def _apply_theme(self) -> None:
        """Faerbt das laufende Programm sofort im neu gewaehlten Design um,
        ohne Neustart.

        `theme.set_theme` traegt die Palette in die Modulvariablen ein, an
        denen sowohl das eigene Stylesheet als auch das der QApplication
        haengen - letzteres, weil Dialoge (Einstellungen, Meldungen, der
        Startdialog) sich nicht selbst stylen, sondern es von dort erben.
        Was ausserhalb jedes Stylesheets direkt gesetzt ist - der Schein
        um den Titel, die Spaltenfarben, Kopf- und Statuszeile -, wird
        einmal neu gezeichnet.
        """
        theme.set_theme(self.config.app_theme)
        sheet = theme.stylesheet()
        app = QApplication.instance()
        if app is not None:
            app.setStyleSheet(sheet)
        self.setStyleSheet(sheet)
        self.title_label.setGraphicsEffect(self._phosphor_glow(22))
        self.search_prompt.setStyleSheet(f"color: {theme.GREEN}; font-weight: bold;")
        self._update_column_marks()
        self._update_header()
        self._update_status()

    # --- Automatischer Shutdown -------------------------------------------

    def _on_shutdown_clicked(self) -> None:
        """Ein Klick fragt je nachdem, was der Knopf gerade zeigt: startet
        er einen Shutdown, oder bricht er den laufenden ab."""
        if self.config.shutdown_at > time.time():
            self._cancel_shutdown()
        else:
            self._start_shutdown()

    def _start_shutdown(self) -> None:
        minutes = dialogs.ask_shutdown_minutes(self)
        if minutes is None:
            return
        try:
            runner.schedule_shutdown(minutes)
        except runner.RunnerError as exc:
            dialogs.show_error(self, str(exc))
            return
        self.config.shutdown_at = time.time() + minutes * 60
        self.config.save(self.config_path)
        self._sync_shutdown_ui()

    def _cancel_shutdown(self) -> None:
        when = time.strftime("%H:%M", time.localtime(self.config.shutdown_at))
        if not dialogs.confirm_cancel_shutdown(self, when):
            return
        try:
            runner.cancel_shutdown()
        except runner.RunnerError as exc:
            dialogs.show_error(self, str(exc))
            return
        self.config.shutdown_at = 0.0
        self.config.save(self.config_path)
        self._sync_shutdown_ui()

    def _on_shutdown_tick(self) -> None:
        """Laeuft jede Sekunde, waehrend ein Shutdown geplant ist.

        Ist die Zeit um, faehrt Windows gerade selbst herunter - oder der
        Countdown wurde ausserhalb von HQ schon abgebrochen. Beides soll
        den Knopf nicht fuer immer rot stehen lassen.
        """
        if self.config.shutdown_at <= time.time():
            self.config.shutdown_at = 0.0
            self.config.save(self.config_path)
            self._sync_shutdown_ui()
            return
        self._update_status()

    def _shutdown_status_text(self) -> str:
        remaining = max(0, int(self.config.shutdown_at - time.time()))
        minutes, seconds = divmod(remaining, 60)
        when = time.strftime("%H:%M", time.localtime(self.config.shutdown_at))
        return tr(
            "> Schaltet aus um {when}  ·  Verbleibend: {left}",
            when=when,
            left=f"{minutes:02d}:{seconds:02d}",
        )

    def _sync_shutdown_ui(self) -> None:
        """Bringt Knopf, Timer und Statuszeile auf den Stand von `config`.

        Auch beim Start gerufen: ein beim letzten Mal geplanter Shutdown
        lief in Windows weiter, auch waehrend HQ zu war, und soll nach dem
        Neustart wieder als aktiv zu sehen sein.
        """
        active = self.config.shutdown_at > time.time()
        self.shutdown_button.setObjectName("danger" if active else "")
        self.shutdown_button.style().unpolish(self.shutdown_button)
        self.shutdown_button.style().polish(self.shutdown_button)
        if active:
            self._shutdown_timer.start(1000)
        else:
            self._shutdown_timer.stop()
        self._update_status()

    def _context_menu(self) -> QMenu:
        """Das Menue zum ausgewaehlten Projekt.

        Getrennt vom Anzeigen, damit sich sein Inhalt pruefen laesst, ohne
        ein Menue zu oeffnen - `exec` wartet auf eine Auswahl.
        """
        project = self._selected()
        pinned = project is not None and self.config.is_favorite(project.name)
        menu = QMenu(self)
        for text, slot in (
            ("Starten", self._start),
            (
                "Favorit lösen" if pinned else "Als Favorit anheften",
                self._toggle_favorite,
            ),
            ("Neues Projekt", self._new_project),
            ("Umbenennen", self._rename),
            ("Ordner öffnen", self._open_explorer),
            ("Terminal hier", self._open_terminal),
            ("Terminal hier (Administrator)", self._open_terminal_admin),
            ("In VS Code öffnen", self._open_vscode),
            ("Aufgaben öffnen", self._open_note),
            ("Stand einfügen", self._insert_status),
        ):
            action = QAction(tr(text), self)
            action.triggered.connect(slot)
            menu.addAction(action)
        menu.addSeparator()
        delete_action = QAction(tr("Löschen"), self)
        delete_action.triggered.connect(self._delete)
        menu.addAction(delete_action)
        return menu

    def _show_menu(self, position) -> None:
        if self._selected() is None:
            return
        self._context_menu().exec(self.list.mapToGlobal(position))

    # --- Qt-Ereignisse --------------------------------------------------

    def event(self, event) -> bool:
        # Zurueck im Fenster: draussen kann inzwischen ein Projektordner
        # entstanden oder verschwunden sein. Ein Scan kostet wenig, und die
        # Liste soll nicht veraltet dastehen.
        if event.type() == QEvent.WindowActivate:
            self._rescan()
        return super().event(event)

    def showEvent(self, event) -> None:  # noqa: N802 (Qt-Namensschema)
        super().showEvent(event)
        # Erst jetzt steht die gestylte Schrift endgueltig fest.
        self._size_columns()

    def resizeEvent(self, event) -> None:  # noqa: N802 (Qt-Namensschema)
        super().resizeEvent(event)
        if self.overlay is None:
            return
        self.overlay.resize_to_parent()
        self._set_elided(self.subtitle, self._header_text)
        self._set_elided(self.status, self._status_text)
