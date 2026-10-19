"""Sprachen der Oberflaeche.

Der deutsche Text ist zugleich der Schluessel: `tr("Löschen")` liefert in
der gewaehlten Sprache die Uebersetzung, und fehlt sie, den deutschen Text
selbst. Der Code liest sich damit weiter wie vorher, und ein vergessener
Eintrag zeigt Deutsch statt eines leeren Knopfes.

Platzhalter stehen in geschweiften Klammern und werden mit `tr(text,
name=wert)` gefuellt. `tests/test_i18n.py` prueft, dass jede Sprache jeden
Text kennt und dieselben Platzhalter benutzt.

Wie `theme` ohne Qt-Importe und mit einer Modulvariablen fuer den Stand:
`set_language` gilt ab dem naechsten `tr`-Aufruf.
"""

from __future__ import annotations

LANGUAGES = ("de", "en", "bhs", "tr", "es")
DEFAULT_LANGUAGE = "de"

#: Jede Sprache in sich selbst benannt - wer sie sucht, kann die anderen
#: vielleicht nicht lesen.
LANGUAGE_LABELS = {
    "de": "DEUTSCH",
    "en": "ENGLISH",
    "bhs": "BOSANSKI / HRVATSKI / SRPSKI",
    "tr": "TÜRKÇE",
    "es": "ESPAÑOL",
}

_language = DEFAULT_LANGUAGE


def resolve_language(language: object) -> str:
    """Unbekanntes wird zur Vorgabe, statt den Start zu kippen."""
    return language if language in LANGUAGES else DEFAULT_LANGUAGE


def set_language(language: str) -> None:
    global _language
    _language = resolve_language(language)


def current_language() -> str:
    return _language


def tr(text: str, **values: object) -> str:
    """`text` in der gewaehlten Sprache, mit eingesetzten Platzhaltern."""
    translated = TRANSLATIONS.get(text, {}).get(_language, text)
    return translated.format(**values) if values else translated


#: Deutscher Text -> {Sprache: Uebersetzung}. Deutsch selbst steht nicht
#: darin, es ist der Schluessel.
#:
#: Spaltenkoepfe muessen samt Sortierpfeil in ihre Spalte passen (Breiten
#: in `ui/window.py`, `COLUMNS`), die Knoepfe des Seitenmenues in 190 px.
TRANSLATIONS: dict[str, dict[str, str]] = {
    # --- Hauptfenster: Spalten ------------------------------------------
    "PROJEKT": {"en": "PROJECT", "bhs": "PROJEKAT", "tr": "PROJE", "es": "PROYECTO"},
    "TYP": {"en": "TYPE", "bhs": "TIP", "tr": "TÜR", "es": "TIPO"},
    "AGENT": {"en": "AGENT", "bhs": "AGENT", "tr": "AJAN", "es": "AGENTE"},
    "NOTIZ": {"en": "NOTE", "bhs": "BILJ.", "tr": "NOT", "es": "NOTA"},
    "ERSTELLT": {"en": "CREATED", "bhs": "KREIRANO", "tr": "OLUŞTURMA", "es": "CREADO"},
    "BEARBEITET": {"en": "MODIFIED", "bhs": "IZMIJENJENO", "tr": "DÜZENLEME", "es": "MODIFICADO"},
    # --- Hauptfenster: Kopf, Suche, Status ------------------------------
    "Einstellungen": {"en": "Settings", "bhs": "Postavke", "tr": "Ayarlar", "es": "Ajustes"},
    "suchen ...": {"en": "search ...", "bhs": "traži ...", "tr": "ara ...", "es": "buscar ..."},
    "{count} PROJEKTE": {
        "en": "{count} PROJECTS",
        "bhs": "{count} PROJEKATA",
        "tr": "{count} PROJE",
        "es": "{count} PROYECTOS",
    },
    "ORDNER NICHT GEFUNDEN — 'EINSTELLUNGEN'": {
        "en": "FOLDER NOT FOUND — 'SETTINGS'",
        "bhs": "MAPA NIJE PRONAĐENA — 'POSTAVKE'",
        "tr": "KLASÖR BULUNAMADI — 'AYARLAR'",
        "es": "CARPETA NO ENCONTRADA — 'AJUSTES'",
    },
    "> kein Projekt ausgewählt": {
        "en": "> no project selected",
        "bhs": "> nijedan projekat nije odabran",
        "tr": "> proje seçilmedi",
        "es": "> ningún proyecto seleccionado",
    },
    "Kein Projekt ausgewählt.": {
        "en": "No project selected.",
        "bhs": "Nijedan projekat nije odabran.",
        "tr": "Proje seçilmedi.",
        "es": "Ningún proyecto seleccionado.",
    },
    "> Schaltet aus um {when}  ·  Verbleibend: {left}": {
        "en": "> Shutting down at {when}  ·  Remaining: {left}",
        "bhs": "> Gašenje u {when}  ·  Preostalo: {left}",
        "tr": "> Kapanış saati {when}  ·  Kalan: {left}",
        "es": "> Se apaga a las {when}  ·  Restante: {left}",
    },
    # --- Hauptfenster: Seitenmenue und untere Leiste --------------------
    "▶ START  F5": {"en": "▶ START  F5", "bhs": "▶ POKRENI  F5", "tr": "▶ BAŞLAT  F5", "es": "▶ INICIAR  F5"},
    "+ NEU  Strg+N": {"en": "+ NEW  Ctrl+N", "bhs": "+ NOVO  Ctrl+N", "tr": "+ YENİ  Ctrl+N", "es": "+ NUEVO  Ctrl+N"},
    "UMBENENNEN  F2": {"en": "RENAME  F2", "bhs": "PREIMENUJ  F2", "tr": "AD DEĞİŞTİR  F2", "es": "RENOMBRAR  F2"},
    "ORDNER": {"en": "FOLDER", "bhs": "MAPA", "tr": "KLASÖR", "es": "CARPETA"},
    "TERMINAL  F4": {"en": "TERMINAL  F4", "bhs": "TERMINAL  F4", "tr": "TERMİNAL  F4", "es": "TERMINAL  F4"},
    "VS CODE": {"en": "VS CODE", "bhs": "VS CODE", "tr": "VS CODE", "es": "VS CODE"},
    "⏻ SHUTDOWN": {"en": "⏻ SHUTDOWN", "bhs": "⏻ GAŠENJE", "tr": "⏻ KAPAT", "es": "⏻ APAGAR"},
    "LÖSCHEN  ENTF": {"en": "DELETE  DEL", "bhs": "OBRIŠI  DEL", "tr": "SİL  DEL", "es": "ELIMINAR  SUPR"},
    # --- Hauptfenster: Rechtsklick-Menue --------------------------------
    "Starten": {"en": "Start", "bhs": "Pokreni", "tr": "Başlat", "es": "Iniciar"},
    "Favorit lösen": {"en": "Unpin favourite", "bhs": "Ukloni iz favorita", "tr": "Favoriden çıkar", "es": "Quitar de favoritos"},
    "Als Favorit anheften": {"en": "Pin as favourite", "bhs": "Prikači kao favorit", "tr": "Favori olarak sabitle", "es": "Fijar como favorito"},
    "Neues Projekt": {"en": "New project", "bhs": "Novi projekat", "tr": "Yeni proje", "es": "Nuevo proyecto"},
    "Umbenennen": {"en": "Rename", "bhs": "Preimenuj", "tr": "Adını değiştir", "es": "Renombrar"},
    "Ordner öffnen": {"en": "Open folder", "bhs": "Otvori mapu", "tr": "Klasörü aç", "es": "Abrir carpeta"},
    "Terminal hier": {"en": "Terminal here", "bhs": "Terminal ovdje", "tr": "Burada terminal", "es": "Terminal aquí"},
    "Terminal hier (Administrator)": {
        "en": "Terminal here (administrator)",
        "bhs": "Terminal ovdje (administrator)",
        "tr": "Burada terminal (yönetici)",
        "es": "Terminal aquí (administrador)",
    },
    "In VS Code öffnen": {"en": "Open in VS Code", "bhs": "Otvori u VS Code", "tr": "VS Code'da aç", "es": "Abrir en VS Code"},
    "Aufgaben öffnen": {"en": "Open tasks", "bhs": "Otvori zadatke", "tr": "Görevleri aç", "es": "Abrir tareas"},
    "Stand einfügen": {"en": "Insert status", "bhs": "Umetni stanje", "tr": "Durumu ekle", "es": "Insertar estado"},
    "Löschen": {"en": "Delete", "bhs": "Obriši", "tr": "Sil", "es": "Eliminar"},
    # --- Dialoge: allgemein ---------------------------------------------
    "OK": {"en": "OK", "bhs": "OK", "tr": "TAMAM", "es": "ACEPTAR"},
    "ABBRECHEN": {"en": "CANCEL", "bhs": "ODUSTANI", "tr": "İPTAL", "es": "CANCELAR"},
    "FEHLER": {"en": "ERROR", "bhs": "GREŠKA", "tr": "HATA", "es": "ERROR"},
    # --- Startdialog ----------------------------------------------------
    "WOMIT STARTEN?": {"en": "START WITH?", "bhs": "POKRENUTI SA?", "tr": "NEYLE BAŞLATILSIN?", "es": "¿INICIAR CON?"},
    "> PROJEKT:  {name}": {
        "en": "> PROJECT:  {name}",
        "bhs": "> PROJEKAT:  {name}",
        "tr": "> PROJE:  {name}",
        "es": "> PROYECTO:  {name}",
    },
    "> KONSOLE": {"en": "> CONSOLE", "bhs": "> KONZOLA", "tr": "> KONSOL", "es": "> CONSOLA"},
    "ALS ADMINISTRATOR": {"en": "AS ADMINISTRATOR", "bhs": "KAO ADMINISTRATOR", "tr": "YÖNETİCİ OLARAK", "es": "COMO ADMINISTRADOR"},
    "OHNE RÜCKFRAGEN   {flags}": {
        "en": "NO CONFIRMATIONS   {flags}",
        "bhs": "BEZ POTVRDE   {flags}",
        "tr": "ONAY SORMADAN   {flags}",
        "es": "SIN CONFIRMACIONES   {flags}",
    },
    "START": {"en": "START", "bhs": "POKRENI", "tr": "BAŞLAT", "es": "INICIAR"},
    # --- Einstellungen --------------------------------------------------
    "EINSTELLUNGEN": {"en": "SETTINGS", "bhs": "POSTAVKE", "tr": "AYARLAR", "es": "AJUSTES"},
    "> KONSOLE, IN DER EIN PROJEKT STARTET": {
        "en": "> CONSOLE A PROJECT STARTS IN",
        "bhs": "> KONZOLA U KOJOJ SE PROJEKAT POKREĆE",
        "tr": "> PROJENİN BAŞLADIĞI KONSOL",
        "es": "> CONSOLA EN LA QUE SE INICIA UN PROYECTO",
    },
    "CRT   GRÜN AUF SCHWARZ": {
        "en": "CRT   GREEN ON BLACK",
        "bhs": "CRT   ZELENO NA CRNOM",
        "tr": "CRT   SİYAH ÜZERİNE YEŞİL",
        "es": "CRT   VERDE SOBRE NEGRO",
    },
    "KLASSISCH   WINDOWS-STANDARD": {
        "en": "CLASSIC   WINDOWS DEFAULT",
        "bhs": "KLASIČNO   WINDOWS STANDARD",
        "tr": "KLASİK   WINDOWS VARSAYILANI",
        "es": "CLÁSICO   PREDETERMINADO DE WINDOWS",
    },
    "> DESIGN DER OBERFLÄCHE": {
        "en": "> INTERFACE DESIGN",
        "bhs": "> IZGLED SUČELJA",
        "tr": "> ARAYÜZ TASARIMI",
        "es": "> DISEÑO DE LA INTERFAZ",
    },
    "GRÜN   STANDARD": {"en": "GREEN   DEFAULT", "bhs": "ZELENO   STANDARD", "tr": "YEŞİL   VARSAYILAN", "es": "VERDE   PREDETERMINADO"},
    "DOS / WINDOWS   BLAU": {"en": "DOS / WINDOWS   BLUE", "bhs": "DOS / WINDOWS   PLAVO", "tr": "DOS / WINDOWS   MAVİ", "es": "DOS / WINDOWS   AZUL"},
    "HACKER   NEONGRÜN": {"en": "HACKER   NEON GREEN", "bhs": "HACKER   NEONSKO ZELENO", "tr": "HACKER   NEON YEŞİL", "es": "HACKER   VERDE NEÓN"},
    "GRAU   AUGENSCHONEND": {"en": "GRAY   EASY ON THE EYES", "bhs": "SIVO   UGODNO ZA OČI", "tr": "GRİ   GÖZ YORMAYAN", "es": "GRIS   SUAVE PARA LA VISTA"},
    "> SPRACHE": {"en": "> LANGUAGE", "bhs": "> JEZIK", "tr": "> DİL", "es": "> IDIOMA"},
    "> PROJEKTORDNER": {"en": "> PROJECTS FOLDER", "bhs": "> MAPA PROJEKATA", "tr": "> PROJE KLASÖRÜ", "es": "> CARPETA DE PROYECTOS"},
    "ÄNDERN ...": {"en": "CHANGE ...", "bhs": "PROMIJENI ...", "tr": "DEĞİŞTİR ...", "es": "CAMBIAR ..."},
    "Projektordner wählen": {
        "en": "Choose projects folder",
        "bhs": "Odaberi mapu projekata",
        "tr": "Proje klasörünü seç",
        "es": "Elegir carpeta de proyectos",
    },
    # --- Shutdown -------------------------------------------------------
    "AUTOMATISCHER SHUTDOWN": {
        "en": "AUTOMATIC SHUTDOWN",
        "bhs": "AUTOMATSKO GAŠENJE",
        "tr": "OTOMATİK KAPATMA",
        "es": "APAGADO AUTOMÁTICO",
    },
    "> IN WIE VIELEN MINUTEN HERUNTERFAHREN?": {
        "en": "> SHUT DOWN IN HOW MANY MINUTES?",
        "bhs": "> UGASITI ZA KOLIKO MINUTA?",
        "tr": "> KAÇ DAKİKA SONRA KAPATILSIN?",
        "es": "> ¿APAGAR EN CUÁNTOS MINUTOS?",
    },
    "{minutes} MINUTEN": {
        "en": "{minutes} MINUTES",
        "bhs": "{minutes} MINUTA",
        "tr": "{minutes} DAKİKA",
        "es": "{minutes} MINUTOS",
    },
    "EIGENE EINGABE ...": {"en": "CUSTOM ...", "bhs": "VLASTITI UNOS ...", "tr": "ÖZEL GİRİŞ ...", "es": "PERSONALIZADO ..."},
    "Minuten": {"en": "Minutes", "bhs": "Minute", "tr": "Dakika", "es": "Minutos"},
    "Bitte eine positive Minutenzahl eingeben.": {
        "en": "Please enter a positive number of minutes.",
        "bhs": "Unesite pozitivan broj minuta.",
        "tr": "Lütfen pozitif bir dakika sayısı girin.",
        "es": "Introduce un número positivo de minutos.",
    },
    "SHUTDOWN ABBRECHEN": {
        "en": "CANCEL SHUTDOWN",
        "bhs": "OTKAŽI GAŠENJE",
        "tr": "KAPATMAYI İPTAL ET",
        "es": "CANCELAR APAGADO",
    },
    "> Automatisches Herunterfahren um {when} Uhr": {
        "en": "> Automatic shutdown at {when}",
        "bhs": "> Automatsko gašenje u {when}",
        "tr": "> Otomatik kapatma saati {when}",
        "es": "> Apagado automático a las {when}",
    },
    "Wirklich abbrechen?": {
        "en": "Really cancel?",
        "bhs": "Zaista otkazati?",
        "tr": "Gerçekten iptal edilsin mi?",
        "es": "¿Cancelar de verdad?",
    },
    "JA, ABBRECHEN": {"en": "YES, CANCEL", "bhs": "DA, OTKAŽI", "tr": "EVET, İPTAL ET", "es": "SÍ, CANCELAR"},
    "NEIN": {"en": "NO", "bhs": "NE", "tr": "HAYIR", "es": "NO"},
    # --- Umbenennen, neu, loeschen --------------------------------------
    "PROJEKT UMBENENNEN": {"en": "RENAME PROJECT", "bhs": "PREIMENUJ PROJEKAT", "tr": "PROJEYİ YENİDEN ADLANDIR", "es": "RENOMBRAR PROYECTO"},
    "> Neuer Name für '{name}':": {
        "en": "> New name for '{name}':",
        "bhs": "> Novi naziv za '{name}':",
        "tr": "> '{name}' için yeni ad:",
        "es": "> Nuevo nombre para '{name}':",
    },
    "NEUES PROJEKT": {"en": "NEW PROJECT", "bhs": "NOVI PROJEKAT", "tr": "YENİ PROJE", "es": "NUEVO PROYECTO"},
    "> Name des neuen Projekts:": {
        "en": "> Name of the new project:",
        "bhs": "> Naziv novog projekta:",
        "tr": "> Yeni projenin adı:",
        "es": "> Nombre del nuevo proyecto:",
    },
    "LÖSCHEN BESTÄTIGEN": {"en": "CONFIRM DELETION", "bhs": "POTVRDI BRISANJE", "tr": "SİLMEYİ ONAYLA", "es": "CONFIRMAR ELIMINACIÓN"},
    "PFAD": {"en": "PATH", "bhs": "PUTANJA", "tr": "YOL", "es": "RUTA"},
    "GRÖSSE": {"en": "SIZE", "bhs": "VELIČINA", "tr": "BOYUT", "es": "TAMAÑO"},
    "In den Papierkorb verschieben?": {
        "en": "Move to the recycle bin?",
        "bhs": "Premjestiti u koš za smeće?",
        "tr": "Geri dönüşüm kutusuna taşınsın mı?",
        "es": "¿Mover a la papelera de reciclaje?",
    },
    "IN DEN PAPIERKORB": {"en": "TO RECYCLE BIN", "bhs": "U KOŠ", "tr": "ÇÖP KUTUSUNA", "es": "A LA PAPELERA"},
    # --- Startbildschirm ------------------------------------------------
    "Speichertest .............. OK": {
        "en": "Memory test ............... OK",
        "bhs": "Test memorije ............. OK",
        "tr": "Bellek testi .............. OK",
        "es": "Prueba de memoria ......... OK",
    },
    "Dateisystem ............... OK": {
        "en": "File system ............... OK",
        "bhs": "Datotečni sustav .......... OK",
        "tr": "Dosya sistemi ............. OK",
        "es": "Sistema de archivos ....... OK",
    },
    "Projektindex .............. OK": {
        "en": "Project index ............. OK",
        "bhs": "Indeks projekata .......... OK",
        "tr": "Proje dizini .............. OK",
        "es": "Índice de proyectos ....... OK",
    },
    "Terminal-Emulation ........ OK": {
        "en": "Terminal emulation ........ OK",
        "bhs": "Emulacija terminala ....... OK",
        "tr": "Terminal öykünmesi ........ OK",
        "es": "Emulación de terminal ..... OK",
    },
    "Starte CODE/X HQ ...": {
        "en": "Starting CODE/X HQ ...",
        "bhs": "Pokrećem CODE/X HQ ...",
        "tr": "CODE/X HQ başlatılıyor ...",
        "es": "Iniciando CODE/X HQ ...",
    },
    "[ Klick oder Taste zum Überspringen ]": {
        "en": "[ Click or press a key to skip ]",
        "bhs": "[ Klik ili tipka za preskakanje ]",
        "tr": "[ Atlamak için tıklayın veya bir tuşa basın ]",
        "es": "[ Haz clic o pulsa una tecla para saltar ]",
    },
    # --- Fehlermeldungen aus `runner` -----------------------------------
    "Der Start als Administrator wurde abgelehnt.": {
        "en": "Starting as administrator was declined.",
        "bhs": "Pokretanje kao administrator je odbijeno.",
        "tr": "Yönetici olarak başlatma reddedildi.",
        "es": "Se rechazó el inicio como administrador.",
    },
    "Start als Administrator fehlgeschlagen (Code {code}).": {
        "en": "Starting as administrator failed (code {code}).",
        "bhs": "Pokretanje kao administrator nije uspjelo (kod {code}).",
        "tr": "Yönetici olarak başlatma başarısız (kod {code}).",
        "es": "Falló el inicio como administrador (código {code}).",
    },
    "Start fehlgeschlagen: {reason}": {
        "en": "Start failed: {reason}",
        "bhs": "Pokretanje nije uspjelo: {reason}",
        "tr": "Başlatma başarısız: {reason}",
        "es": "Error al iniciar: {reason}",
    },
    "Papierkorb-Vorgang fehlgeschlagen (Code {code}).": {
        "en": "Recycle bin operation failed (code {code}).",
        "bhs": "Premještanje u koš nije uspjelo (kod {code}).",
        "tr": "Geri dönüşüm kutusu işlemi başarısız (kod {code}).",
        "es": "Falló la operación de la papelera (código {code}).",
    },
    "Ordner '{path}' existiert nicht mehr.": {
        "en": "Folder '{path}' no longer exists.",
        "bhs": "Mapa '{path}' više ne postoji.",
        "tr": "'{path}' klasörü artık yok.",
        "es": "La carpeta '{path}' ya no existe.",
    },
    "{label} ('{agent}') wurde im PATH nicht gefunden.": {
        "en": "{label} ('{agent}') was not found in PATH.",
        "bhs": "{label} ('{agent}') nije pronađen u PATH-u.",
        "tr": "{label} ('{agent}') PATH içinde bulunamadı.",
        "es": "{label} ('{agent}') no se encontró en el PATH.",
    },
    "Der Name darf nicht leer sein.": {
        "en": "The name must not be empty.",
        "bhs": "Naziv ne smije biti prazan.",
        "tr": "Ad boş olamaz.",
        "es": "El nombre no puede estar vacío.",
    },
    "Unerlaubte Zeichen: {chars}": {
        "en": "Forbidden characters: {chars}",
        "bhs": "Nedozvoljeni znakovi: {chars}",
        "tr": "İzin verilmeyen karakterler: {chars}",
        "es": "Caracteres no permitidos: {chars}",
    },
    "Der Name darf nicht mit Punkt oder Leerzeichen enden.": {
        "en": "The name must not end with a dot or a space.",
        "bhs": "Naziv ne smije završavati točkom ili razmakom.",
        "tr": "Ad nokta veya boşlukla bitemez.",
        "es": "El nombre no puede terminar en punto o espacio.",
    },
    "'{name}' ist ein reservierter Windows-Name.": {
        "en": "'{name}' is a reserved Windows name.",
        "bhs": "'{name}' je rezervirani Windows naziv.",
        "tr": "'{name}' ayrılmış bir Windows adıdır.",
        "es": "'{name}' es un nombre reservado de Windows.",
    },
    "'{name}' existiert bereits.": {
        "en": "'{name}' already exists.",
        "bhs": "'{name}' već postoji.",
        "tr": "'{name}' zaten var.",
        "es": "'{name}' ya existe.",
    },
    "Projektordner '{path}' existiert nicht.": {
        "en": "Projects folder '{path}' does not exist.",
        "bhs": "Mapa projekata '{path}' ne postoji.",
        "tr": "'{path}' proje klasörü yok.",
        "es": "La carpeta de proyectos '{path}' no existe.",
    },
    "Anlegen fehlgeschlagen: {reason}": {
        "en": "Creating failed: {reason}",
        "bhs": "Kreiranje nije uspjelo: {reason}",
        "tr": "Oluşturma başarısız: {reason}",
        "es": "Error al crear: {reason}",
    },
    "Umbenennen fehlgeschlagen: {reason}": {
        "en": "Renaming failed: {reason}",
        "bhs": "Preimenovanje nije uspjelo: {reason}",
        "tr": "Yeniden adlandırma başarısız: {reason}",
        "es": "Error al renombrar: {reason}",
    },
    "Ordner laesst sich nicht oeffnen: {reason}": {
        "en": "Folder cannot be opened: {reason}",
        "bhs": "Mapa se ne može otvoriti: {reason}",
        "tr": "Klasör açılamıyor: {reason}",
        "es": "No se puede abrir la carpeta: {reason}",
    },
    "Notiz laesst sich nicht schreiben: {reason}": {
        "en": "Note cannot be written: {reason}",
        "bhs": "Bilješka se ne može zapisati: {reason}",
        "tr": "Not yazılamıyor: {reason}",
        "es": "No se puede escribir la nota: {reason}",
    },
    "Notiz laesst sich nicht lesen: {reason}": {
        "en": "Note cannot be read: {reason}",
        "bhs": "Bilješka se ne može pročitati: {reason}",
        "tr": "Not okunamıyor: {reason}",
        "es": "No se puede leer la nota: {reason}",
    },
    "VS Code ('code') wurde im PATH nicht gefunden.": {
        "en": "VS Code ('code') was not found in PATH.",
        "bhs": "VS Code ('code') nije pronađen u PATH-u.",
        "tr": "VS Code ('code') PATH içinde bulunamadı.",
        "es": "VS Code ('code') no se encontró en el PATH.",
    },
}
