"""Was am Stylesheet nicht nur Geschmack ist.

Farben und Abstaende sind Entscheidungen und werden hier nicht geprueft.
Geprueft wird, wo eine Stilregel die Ausrichtung der Liste verschieben
wuerde - denn die Spalten stehen nur dann unter ihren Ueberschriften,
wenn jede Zeile gleich weit eingerueckt ist.
"""

import re

from projecthq.theme import LIST_BORDER, ROW_MARKER, ROW_PADDING, stylesheet


def rule(selector: str) -> str:
    """Der Inhalt der Regel zu `selector`."""
    match = re.search(re.escape(selector) + r"\s*\{([^}]*)\}", stylesheet())
    assert match is not None, f"Regel '{selector}' fehlt im Stylesheet"
    return match.group(1)


def border_left(selector: str) -> str:
    """Breite des linken Rands einer Regel, '0px' wenn sie keinen setzt."""
    match = re.search(r"border-left:\s*(\S+)", rule(selector))
    return match.group(1) if match else "0px"


def test_selecting_a_row_does_not_shift_its_text():
    """Die Auswahl darf den linken Rand nur faerben, nicht erst schaffen.

    Bekommt ihn allein die ausgewaehlte Zeile, rueckt deren Text um seine
    Breite nach rechts - und ihre Spalten stehen als einzige neben den
    Ueberschriften statt darunter.
    """
    assert border_left("QListWidget::item") == border_left(
        "QListWidget::item:selected"
    )


def test_the_stylesheet_uses_the_published_row_metrics():
    """Die Masse einer Zeile stehen als Konstanten bereit.

    Der Spaltenkopf rechnet seinen Einzug daraus aus. Weichen Stylesheet
    und Konstanten voneinander ab, stimmt er nicht mehr - deshalb sind
    beide hier aneinander gebunden.
    """
    assert border_left("QListWidget::item") == f"{ROW_MARKER}px"
    assert f"padding: 7px {ROW_PADDING}px" in rule("QListWidget::item")
    assert f"border: {LIST_BORDER}px" in rule("QListWidget")


def test_the_checkbox_looks_like_a_radio_button():
    """Beide Indikatoren sind eckig und teilen sich eine Regel.

    Ohne eigene Regel malt Windows sein Standardkaestchen - mit rundem
    Haken und grauem Rahmen, das einzige Fremdteil in einem Dialog, der
    sonst durchgehend im Terminal-Look steht.
    """
    assert rule("QCheckBox::indicator") == rule("QRadioButton::indicator")
    assert rule("QCheckBox::indicator:checked") == rule(
        "QRadioButton::indicator:checked"
    )
