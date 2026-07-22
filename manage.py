# Dateiname: manage.py
# Beschreibung: Diese Datei startet die Verwaltungsbefehle für das Django Projekt. Damit können zum Beispiel der Entwicklungsserver und Änderungen an der Datenbank ausgeführt werden.

import os
import sys


def hauptprogramm():
    """Diese Funktion lädt die Einstellungen und führt den eingegebenen Verwaltungsbefehl aus."""
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "datenvisualisierung.settings")
    try:
        from django.core.management import execute_from_command_line
    except ImportError as fehler:
        raise ImportError(
            "Django konnte nicht importiert werden. Prüfe, ob Django installiert ist "
            "und ob die virtuelle Umgebung aktiviert wurde."
        ) from fehler
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    hauptprogramm()
