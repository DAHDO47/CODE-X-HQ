"""Einstiegspunkt von CODE/X HQ."""

from __future__ import annotations

import sys

from PySide6.QtWidgets import QApplication

from projecthq import i18n, theme
from projecthq.config import Config, adopt_legacy, config_location, legacy_location
from projecthq.theme import stylesheet
from projecthq.ui import instance
from projecthq.ui.appicon import apply_app_icon
from projecthq.ui.boot import BootScreen
from projecthq.ui.window import MainWindow


def main() -> int:
    app = QApplication(sys.argv)
    apply_app_icon(app)

    # Laeuft schon einer, gehoert ihm das Feld: zwei Launcher wuerden sich
    # die config.json gegenseitig ueberschreiben. Dieser Start holt dann
    # nur das vorhandene Fenster nach vorn.
    token = instance.claim()
    if token is None:
        instance.wake_running_instance()
        return 0
    app.instance_token = token  # Marke halten, solange das Programm laeuft

    config_path = config_location()
    # Beim ersten Start nach der Umstellung liegt die Datei noch neben der
    # .exe. Von dort wird sie einmalig uebernommen.
    adopt_legacy(config_path, legacy_location())
    config = Config.load(config_path)
    # Erst jetzt steht fest, welches Design gilt - vorher gaebe es nur die
    # Vorgabe, und Dialoge blieben bis zum ersten Oeffnen der Einstellungen
    # in ihr haengen, weil sie das QApplication-weite Stylesheet erben.
    theme.set_theme(config.app_theme)
    app.setStyleSheet(stylesheet())
    # Ebenso die Sprache: schon der Startbildschirm spricht sie.
    i18n.set_language(config.language)

    window = MainWindow(config, config_path)

    def on_second_start() -> None:
        connection = server.nextPendingConnection()
        if connection is not None:
            connection.close()
        window.present()

    server = instance.listen()
    server.newConnection.connect(on_second_start)
    app.instance_server = server  # dito: sonst raeumt Python ihn ab

    if "--no-boot" in sys.argv:
        window.present()
    else:
        boot = BootScreen()
        boot.finished.connect(window.present)
        app.boot_screen = boot  # Referenz halten, sonst raeumt Python sie ab
        boot.start()

    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
