import os

# Muss gesetzt sein, bevor irgendein Qt-Modul geladen wird: die Fenstertests
# laufen ohne sichtbaren Bildschirm.
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest

from projecthq import i18n, theme


@pytest.fixture(autouse=True)
def _reset_theme():
    """Setzt das Design nach jedem Test zurueck.

    `theme.set_theme` schreibt in Modulvariablen - ohne Reset saehe ein
    Test, der nach einem Design-Wechsel laeuft, die Farben eines anderen
    Tests statt der Vorgabe.
    """
    yield
    theme.set_theme(theme.DEFAULT_THEME)


@pytest.fixture(autouse=True)
def _reset_language():
    """Aus demselben Grund fuer die Sprache: `i18n.set_language` schreibt
    in eine Modulvariable, und die Tests pruefen deutsche Texte."""
    yield
    i18n.set_language(i18n.DEFAULT_LANGUAGE)
