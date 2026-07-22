# Dateiname: asgi.py
# Beschreibung: Diese Datei stellt das Projekt für einen ASGI Server bereit. Sie wird später für die Veröffentlichung und für gleichzeitige Verbindungen gebraucht.

import os

from django.core.asgi import get_asgi_application


# Django muss vor dem Start wissen, in welcher Datei sich die Einstellungen des Projekts befinden.
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "datenvisualisierung.settings")

application = get_asgi_application()
