# Dateiname: apps.py
# Beschreibung: Diese Datei enthält die grundlegende Konfiguration der Visualisierungs App. Django verwendet sie beim Start, um die App richtig zu laden.

from django.apps import AppConfig


class VisualisierungKonfiguration(AppConfig):
    """Diese Klasse legt den Namen der App und die Art der automatischen Datenbankschlüssel fest."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "visualisierung"
