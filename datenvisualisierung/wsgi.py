# Dateiname: wsgi.py
# Beschreibung: Diese Datei stellt das Projekt für einen WSGI Server bereit. Sie wird gebraucht, wenn das Projekt später auf einem klassischen Webserver läuft.

import os

from django.core.wsgi import get_wsgi_application


# Django muss vor dem Start wissen, in welcher Datei sich die Einstellungen des Projekts befinden.
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "datenvisualisierung.settings")

application = get_wsgi_application()
