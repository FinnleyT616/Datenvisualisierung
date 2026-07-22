# Dateiname: urls.py
# Beschreibung: Diese Datei sammelt die Adressen des ganzen Projekts. Im Moment ist hier nur die Verwaltungsseite von Django eingetragen.

from django.contrib import admin
from django.urls import path


# Django erwartet für die Adressen genau diesen Namen, damit die eingetragenen Seiten gefunden werden können.
urlpatterns = [
    path("admin/", admin.site.urls),
]
