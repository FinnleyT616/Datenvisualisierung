# Dateiname: settings.py
# Beschreibung: Diese Datei enthält die Einstellungen für das ganze Django Projekt. Sie legt unter anderem die Sprache, die Zeitzone und die Ordner für statische Dateien und Medien fest.

from pathlib import Path


# Dieser Pfad zeigt auf den Hauptordner des Projekts und wird für alle weiteren Ordner verwendet.
BASE_DIR = Path(__file__).resolve().parent.parent

# Dieser geheime Schlüssel wird während der Entwicklung von Django benötigt und darf später nicht öffentlich bekannt sein.
SECRET_KEY = "django-insecure-j6ml$-i8t9om#wpx71jedtyn71#c*v8u7t_y=upbv_%m082qpc"

# Diese Einstellung zeigt während der Entwicklung ausführliche Fehlermeldungen an und muss vor der Veröffentlichung ausgeschaltet werden.
DEBUG = True

ALLOWED_HOSTS = []

# In dieser Liste stehen alle eingebauten Django Apps und die eigene App für die Visualisierungen.
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "visualisierung",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "datenvisualisierung.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "datenvisualisierung.wsgi.application"

# Für die Entwicklung wird eine einfache Datenbankdatei direkt im Projektordner gespeichert.
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

# Diese Prüfungen helfen dabei, zu einfache oder unsichere Passwörter bei der Eingabe zu erkennen.
AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

# Die Sprache und die Zeitzone sind auf die deutschsprachige Schweiz eingestellt.
LANGUAGE_CODE = "de-ch"
TIME_ZONE = "Europe/Zurich"
USE_I18N = True
USE_TZ = True

# Statische Dateien enthalten zum Beispiel eigene Gestaltung, Skripte oder feste Bilder für die Benutzeroberfläche.
STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "static"]

# Hochgeladene Dateien und erzeugte Diagramme werden im Medienordner des Projekts abgelegt.
MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "medien"

# Neue Datenbankeinträge erhalten automatisch eine grosse ganze Zahl als eindeutigen Schlüssel.
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
