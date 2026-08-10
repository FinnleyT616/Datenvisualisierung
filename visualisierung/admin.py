# Dateiname: admin.py
# Beschreibung: Diese Datei ist für Einträge auf der Verwaltungsseite von Django vorgesehen. Später können hier eigene Datenmodelle für die Verwaltung registriert werden.

from django.contrib import admin

from .models import Datensatz, Datenpunkt, Diagramm


# Diese Registrierung zeigt alle drei wichtigen Datenmodelle auf der Verwaltungsseite an. Dadurch können Datensätze, Datenpunkte und Diagramme dort angesehen, erstellt und bearbeitet werden.
admin.site.register([Datensatz, Datenpunkt, Diagramm])
