"""Tests fuer das Anwendungssymbol.

Sie sichern, dass die `.ico` mitgeliefert wird, die von Windows
benoetigten Groessen enthaelt und beim Start tatsaechlich gesetzt wird.
"""

from __future__ import annotations

import pytest
from PySide6.QtCore import QSize
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication

from projecthq.ui import appicon


@pytest.fixture(scope="session")
def app():
    return QApplication.instance() or QApplication([])


def test_icon_is_shipped():
    path = appicon.icon_path()
    assert path is not None, "assets/projecthq.ico fehlt"
    assert path.suffix == ".ico"


def test_icon_contains_taskbar_sizes(app):
    icon = QIcon(str(appicon.icon_path()))
    assert not icon.isNull()
    sizes = {(s.width(), s.height()) for s in icon.availableSizes()}
    # 16 fuer die Taskleiste, 256 fuer grosse Kacheln im Explorer.
    assert (16, 16) in sizes
    assert (256, 256) in sizes


def test_apply_sets_application_icon(app):
    previous = app.windowIcon()
    try:
        assert appicon.apply_app_icon(app) is True
        assert not app.windowIcon().pixmap(QSize(32, 32)).isNull()
    finally:
        app.setWindowIcon(previous)
