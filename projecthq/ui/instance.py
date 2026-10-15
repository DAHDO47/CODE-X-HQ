"""Nur eine laufende Instanz.

Zwei Launcher nebeneinander schreiben sich die `config.json` gegenseitig
zu: jeder haelt seit seinem Start eine eigene Kopie und speichert immer
die ganze Datei. Wer zuletzt speichert, gewinnt - der andere verliert
Sortierung, Projektordner oder Konsolen-Design. Statt die Datei beim
Speichern zusammenzufuehren, gibt es die zweite Instanz gar nicht erst:
ihr Start holt das vorhandene Fenster nach vorn und endet.

Zwei Dinge sind dafuer noetig, und sie brauchen verschiedene Mittel:

*Bin ich der erste?* beantwortet ein benannter Mutex von Windows.
`QLocalServer.listen` taugt dafuer nicht - eine benannte Pipe erlaubt
mehrere Server desselben Namens, der zweite Aufruf gelingt also ebenso.
Der Mutex verschwindet mit dem letzten Prozess, der ihn haelt; ein
Absturz sperrt den naechsten Start deshalb nicht aus.

*Wie sage ich es dem anderen?* uebernimmt eine benannte Pipe von Qt. Sie
traegt keine Nachricht ausser der Verbindung selbst.
"""

from __future__ import annotations

import ctypes
from ctypes import wintypes

from PySide6.QtNetwork import QLocalServer, QLocalSocket

#: Name des Mutex und der Pipe. Beide leben in eigenen Namensraeumen von
#: Windows und kommen sich trotz gleichen Namens nicht ins Gehege.
INSTANCE_NAME = "ProjectHQ.single-instance"

ERROR_ALREADY_EXISTS = 183

_kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
_kernel32.CreateMutexW.argtypes = (wintypes.LPVOID, wintypes.BOOL, wintypes.LPCWSTR)
_kernel32.CreateMutexW.restype = wintypes.HANDLE
_kernel32.CloseHandle.argtypes = (wintypes.HANDLE,)
_kernel32.CloseHandle.restype = wintypes.BOOL


def claim(name: str = INSTANCE_NAME) -> int | None:
    """Belegt den Namen fuer diese Instanz.

    Gibt eine Marke zurueck, die bis zum Programmende aufzuheben ist - oder
    `None`, wenn schon eine Instanz laeuft. Die Marke wird mit `release`
    zurueckgegeben; beim Beenden des Prozesses raeumt Windows sie ohnehin
    selbst weg.
    """
    handle = _kernel32.CreateMutexW(None, False, name)
    if not handle:
        return None
    if ctypes.get_last_error() == ERROR_ALREADY_EXISTS:
        _kernel32.CloseHandle(handle)
        return None
    return handle


def release(token: int | None) -> None:
    """Gibt die Marke aus `claim` zurueck."""
    if token:
        _kernel32.CloseHandle(token)


def listen(name: str = INSTANCE_NAME) -> QLocalServer:
    """Nimmt entgegen, wenn ein spaeterer Start sich meldet.

    Erst nach `claim` aufzurufen: der Mutex stellt sicher, dass es keine
    zweite Instanz gibt, der das Aufraeumen der Pipe die eigene wegnaehme.
    """
    QLocalServer.removeServer(name)
    server = QLocalServer()
    server.listen(name)
    return server


def wake_running_instance(name: str = INSTANCE_NAME, timeout_ms: int = 300) -> bool:
    """Klopft bei der laufenden Instanz an, damit sie ihr Fenster zeigt.

    Meldet, ob jemand geantwortet hat. Ein `False` trotz belegtem Mutex
    hiesse: die andere Instanz startet gerade noch oder haengt - dann ist
    das eigene Ende immer noch besser als ein zweiter Launcher.
    """
    socket = QLocalSocket()
    socket.connectToServer(name)
    if not socket.waitForConnected(timeout_ms):
        return False
    socket.write(b"zeig dich")
    socket.waitForBytesWritten(timeout_ms)
    socket.disconnectFromServer()
    return True
