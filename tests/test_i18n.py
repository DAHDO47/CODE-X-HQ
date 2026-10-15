"""Tests fuer die Sprachen der Oberflaeche."""

from __future__ import annotations

import re
import string
from pathlib import Path

import pytest

from projecthq import i18n
from projecthq.i18n import LANGUAGES, TRANSLATIONS, tr

SOURCE = Path(__file__).resolve().parent.parent / "projecthq"
FOREIGN = [language for language in LANGUAGES if language != i18n.DEFAULT_LANGUAGE]


def _placeholders(text: str) -> set[str]:
    return {name for _lit, name, _spec, _conv in string.Formatter().parse(text) if name}


def test_german_is_the_default():
    assert i18n.current_language() == "de"
    assert tr("Löschen") == "Löschen"


def test_every_text_is_translated_into_every_language():
    missing = [
        (text, language)
        for text, translations in TRANSLATIONS.items()
        for language in FOREIGN
        if not translations.get(language)
    ]
    assert missing == []


def test_translations_use_the_same_placeholders():
    """Ein vertippter Platzhalter fiele sonst erst beim Anzeigen als
    KeyError auf - mitten im Programm."""
    wrong = [
        (text, language)
        for text, translations in TRANSLATIONS.items()
        for language, translated in translations.items()
        if _placeholders(translated) != _placeholders(text)
    ]
    assert wrong == []


def test_every_tr_call_in_the_code_has_an_entry():
    """Ein `tr("...")` ohne Eintrag zeigte in jeder Sprache Deutsch."""
    pattern = re.compile(r'\btr\(\s*"((?:[^"\\]|\\.)*)"')
    unknown = sorted(
        {
            text
            for path in SOURCE.rglob("*.py")
            if path.name != "i18n.py"
            for text in pattern.findall(path.read_text(encoding="utf-8"))
            if text not in TRANSLATIONS
        }
    )
    assert unknown == []


def test_label_tables_are_translatable():
    """Texte, die nicht als Literal in `tr` stehen, sondern in Tabellen."""
    from projecthq.theme import THEME_LABELS
    from projecthq.ui import boot, dialogs, window

    texts = [
        *(title for _key, title, _width in window.COLUMNS),
        *(text for text, _slot in window.MainWindow.SIDEBAR_ACTIONS),
        *dialogs.CONSOLE_LABELS.values(),
        *THEME_LABELS.values(),
        dialogs.CUSTOM_SHUTDOWN_ENTRY,
        *(line for line in boot.LINES if line and not line.startswith("CODE/X HQ BIOS")),
    ]
    assert [text for text in texts if text not in TRANSLATIONS] == []


@pytest.mark.parametrize("language", LANGUAGES)
def test_column_titles_fit_their_columns(language):
    """Samt Sortierpfeil und der freien Stelle am Ende - sonst wuerde die
    Ueberschrift abgeschnitten."""
    from projecthq.ui.window import COLUMNS

    i18n.set_language(language)
    too_wide = [
        tr(title)
        for _key, title, width in COLUMNS
        if width and len(tr(title)) + 2 > width - 1
    ]
    assert too_wide == []


def test_switching_the_language_changes_the_text():
    i18n.set_language("en")
    assert tr("Löschen") == "Delete"
    i18n.set_language("es")
    assert tr("{count} PROJEKTE", count=3) == "3 PROYECTOS"


def test_an_unknown_language_falls_back_to_german():
    i18n.set_language("klingon")
    assert i18n.current_language() == "de"


def test_an_unknown_text_stays_as_it_is():
    i18n.set_language("tr")
    assert tr("Gibt es nicht") == "Gibt es nicht"
