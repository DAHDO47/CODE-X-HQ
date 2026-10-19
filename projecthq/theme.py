"""Farbpaletten und Qt-Stylesheet - mehrere waehlbare Designs.

Andere Module lesen eine Farbe ueber `theme.GREEN` und nicht ueber ein
`from .theme import GREEN` - nur so sehen bereits gebaute Fenster und neu
geoeffnete Dialoge dieselbe, gerade gewechselte Palette. Ein `from`-Import
bindet den Namen einmalig beim Laden des Moduls und liesse sich von einem
spaeteren `set_theme` nicht mehr erreichen.
"""

#: Eine Palette je Design. Wer eine Farbe hinzufuegt, traegt sie hier fuer
#: jedes Design ein - `set_theme` uebernimmt sonst nur einen Teil.
#:
#: BORDER trennt duenne Linien (Titelleiste, Zeilenraender) vom
#: Hintergrund, HOVER und SELECT sind die Listenzeile unter dem Mauszeiger
#: und die ausgewaehlte, DISABLED der abgeblendete Text auf gesperrten
#: Bedienelementen.
THEMES = {
    "green": {
        "BG": "#050b05",
        "PANEL": "#0a140a",
        "GREEN": "#33ff66",
        "DIM": "#1f8a3d",
        "AMBER": "#ffb000",
        "RED": "#ff4444",
        "BORDER": "#0f2a13",
        "HOVER": "#0d2413",
        "SELECT": "#10391b",
        "DISABLED": "#14471f",
    },
    "dos": {
        "BG": "#0000aa",
        "PANEL": "#1a1aae",
        "GREEN": "#ffffff",
        "DIM": "#aaaaaa",
        "AMBER": "#ffff55",
        "RED": "#ff5555",
        "BORDER": "#2e2ec2",
        "HOVER": "#2626c8",
        "SELECT": "#3d3dd6",
        "DISABLED": "#6666bb",
    },
    "hacker": {
        "BG": "#000000",
        "PANEL": "#001a00",
        "GREEN": "#00ff41",
        "DIM": "#00b32d",
        "AMBER": "#ff2bd6",
        "RED": "#ff2a2a",
        "BORDER": "#003300",
        "HOVER": "#002600",
        "SELECT": "#003d00",
        "DISABLED": "#0a5c1a",
    },
    # Fuer lange Sitzungen: mattes Dunkelgrau statt Schwarz, weiches
    # Hellgrau statt leuchtender Schrift, gedaempfte Warnfarben. Der
    # Kontrast bleibt gut lesbar (Text etwa 9:1), blendet aber nicht.
    "gray": {
        "BG": "#26282b",
        "PANEL": "#2d3034",
        "GREEN": "#c9ccd1",
        "DIM": "#878c93",
        "AMBER": "#d2b06c",
        "RED": "#d47a7a",
        "BORDER": "#36393e",
        "HOVER": "#313439",
        "SELECT": "#3c4046",
        "DISABLED": "#55595f",
    },
}
DEFAULT_THEME = "green"

#: Beschriftung im Einstellungen-Dialog.
THEME_LABELS = {
    "green": "GRÜN   STANDARD",
    "dos": "DOS / WINDOWS   BLAU",
    "hacker": "HACKER   NEONGRÜN",
    "gray": "GRAU   AUGENSCHONEND",
}

FONT_FAMILY = "Consolas, 'Cascadia Mono', 'Courier New', monospace"

# Masse einer Listenzeile. Sie stehen hier als Konstanten und nicht nur
# im Stylesheet, weil der Spaltenkopf seinen Einzug daraus ausrechnet
# (siehe `ui/window.py`): Kopf und Zeilen ruecken nur dann gleich weit
# ein, wenn beide von denselben Zahlen ausgehen.
LIST_BORDER = 1  # Rahmen um die Liste
ROW_PADDING = 10  # Innenabstand einer Zeile
ROW_MARKER = 3  # linker Rand jeder Zeile; sichtbar nur bei der Auswahl


def _apply(name: str) -> None:
    """Traegt eine Palette in die Modulvariablen BG, PANEL, GREEN, ... ein."""
    globals().update(THEMES[name])


CURRENT_THEME = DEFAULT_THEME
_apply(CURRENT_THEME)


def set_theme(name: object) -> None:
    """Wechselt das Design. Ein unbekannter Name faellt still auf die
    Vorgabe zurueck - dieselbe Regel wie beim Konsolen-Design in `config`."""
    global CURRENT_THEME
    CURRENT_THEME = name if name in THEMES else DEFAULT_THEME
    _apply(CURRENT_THEME)


def stylesheet() -> str:
    # Das Kaestchen vor einem Radioknopf und vor einer Checkbox. Einmal
    # beschrieben, in beide Regeln eingesetzt: Qt fasst zwei Selektoren
    # zwar mit Komma zusammen, dann steht die Regel aber unter keinem der
    # beiden Namen mehr fuer sich - und genau danach sucht der Test.
    indicator = f"""
        width: 10px;
        height: 10px;
        border: 1px solid {DIM};
        background: {BG};
    """
    indicator_checked = f"""
        background: {GREEN};
        border: 1px solid {GREEN};
    """
    return f"""
    QWidget {{
        background: {BG};
        color: {GREEN};
        font-family: {FONT_FAMILY};
        font-size: 13px;
    }}
    /* Labels erben sonst den Fensterhintergrund. Auf dem helleren Panel
       ergaebe das ein sichtbares Rechteck, und der Phosphorschein legte
       sich um dieses Rechteck statt um die Buchstaben. */
    QLabel {{
        background: transparent;
    }}
    /* Eigener Fensterrahmen. Die Linie aussen malt `Chrome` selbst,
       hier stehen nur Leiste und Knoepfe. */
    QWidget#chromeFrame {{
        background: {BG};
    }}
    QWidget#titlebar {{
        background: transparent;
        border-bottom: 1px solid {BORDER};
    }}
    QLabel#titletext {{
        color: {DIM};
        font-size: 12px;
        letter-spacing: 4px;
    }}
    QPushButton#chrome, QPushButton#chromeClose {{
        background: transparent;
        border: none;
        padding: 0;
        color: {DIM};
        font-size: 14px;
    }}
    QPushButton#chrome:hover {{ background: {DIM}; color: {BG}; }}
    QPushButton#chromeClose:hover {{ background: {RED}; color: {BG}; }}
    QFrame#panel {{
        background: {PANEL};
        border: 1px solid {DIM};
    }}
    QLabel#title {{
        color: {GREEN};
        font-size: 20px;
        font-weight: bold;
        letter-spacing: 6px;
    }}
    /* Spaltenkopf. Die Farben der einzelnen Ueberschriften setzt das
       Fenster selbst, weil die sortierte Spalte hervorgehoben wird. */
    QWidget#columns {{
        background: transparent;
    }}
    QLabel#subtitle, QLabel#status {{
        color: {DIM};
        font-size: 12px;
    }}
    QLineEdit {{
        background: {BG};
        border: 1px solid {DIM};
        padding: 6px 8px;
        color: {GREEN};
        selection-background-color: {DIM};
        selection-color: {BG};
    }}
    QLineEdit:focus {{ border: 1px solid {GREEN}; }}
    QListWidget {{
        background: {BG};
        border: {LIST_BORDER}px solid {DIM};
        outline: none;
    }}
    /* Den linken Rand tragen alle Zeilen, sichtbar ist er nur bei der
       ausgewaehlten. Bekaeme ihn erst die Auswahl, rueckte deren Text um
       seine Breite nach rechts - und ihre Spalten stuenden als einzige
       nicht mehr unter den Ueberschriften. */
    QListWidget::item {{
        padding: 7px {ROW_PADDING}px;
        border-bottom: 1px solid {BORDER};
        border-left: {ROW_MARKER}px solid transparent;
    }}
    QListWidget::item:hover {{ background: {HOVER}; }}
    /* Auswahl faerbt nur den Hintergrund. Die Textfarbe bleibt erhalten,
       damit graue und bernsteinfarbene Eintraege lesbar bleiben. */
    QListWidget::item:selected {{
        background: {SELECT};
        border-left: {ROW_MARKER}px solid {GREEN};
    }}
    QPushButton {{
        background: transparent;
        border: 1px solid {DIM};
        padding: 7px 14px;
        color: {GREEN};
    }}
    QPushButton:hover {{ background: {DIM}; color: {BG}; }}
    QPushButton:disabled {{ color: {DISABLED}; border-color: {DISABLED}; }}
    QPushButton#danger {{ border-color: {RED}; color: {RED}; }}
    QPushButton#danger:hover {{ background: {RED}; color: {BG}; }}
    /* Das Seitenmenue: ein Rahmen um den ganzen Block, die Knoepfe darin
       ohne eigenen Rahmen, nur durch eine Linie getrennt - sonst staende
       zwischen je zwei Knoepfen ein doppelt so breiter Strich. */
    QFrame#sidebar {{
        background: {PANEL};
        border: 1px solid {DIM};
    }}
    QPushButton#sidebarButton {{
        text-align: left;
        border: none;
        border-bottom: 1px solid {BORDER};
        padding: 10px 14px;
    }}
    QPushButton#sidebarButton:hover {{ background: {DIM}; color: {BG}; }}
    /* Das Zahnrad oben rechts im Kopf: ein Knopf ohne das grosszuegige
       Standardpolster, sonst passt das Symbol nicht in seine Ecke. */
    QPushButton#gear {{
        padding: 0;
        font-size: 13px;
    }}
    QPushButton#gear:hover {{ background: {DIM}; color: {BG}; }}
    /* Der Indikator ist eckig, nicht rund: ein runder Punkt waere das
       einzige runde Element im ganzen Programm. Das Kaestchen der
       Checkbox sieht genauso aus - ohne eigene Regel malte Windows sein
       Standardkaestchen, das einzige Fremdteil im Dialog. */
    QRadioButton, QCheckBox {{ spacing: 9px; padding: 2px 0; }}
    QRadioButton::indicator {{{indicator}}}
    QCheckBox::indicator {{{indicator}}}
    QRadioButton::indicator:checked {{{indicator_checked}}}
    QCheckBox::indicator:checked {{{indicator_checked}}}
    QRadioButton:disabled, QCheckBox:disabled {{ color: {DISABLED}; }}
    QMenu {{ background: {PANEL}; border: 1px solid {DIM}; }}
    QMenu::item {{ padding: 6px 22px; }}
    QMenu::item:selected {{ background: {DIM}; color: {BG}; }}
    QScrollBar:vertical {{ background: {BG}; width: 10px; }}
    QScrollBar::handle:vertical {{ background: {DIM}; min-height: 24px; }}
    QScrollBar::add-line, QScrollBar::sub-line {{ height: 0px; }}
    """
