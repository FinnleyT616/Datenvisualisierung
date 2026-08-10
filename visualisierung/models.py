# Dateiname: models.py
# Beschreibung: Diese Datei ist für die Datenmodelle der Visualisierungs App vorgesehen. Die Modelle beschreiben später, welche Informationen in der Datenbank gespeichert werden.

from django.db import models


# Diese Auswahl enthält alle Dateiformate, welche bei einem Datensatz angegeben werden dürfen. Der gespeicherte Wert ist klein geschrieben und der sichtbare Text zeigt das Format deutlich an.
DATEIFORMAT_AUSWAHL = [
    ("csv", "CSV"),
    ("json", "JSON"),
]

# Diese Auswahl enthält genau die drei Diagrammarten, welche das Projekt unterstützt. Weitere Arten werden bewusst nicht angeboten, damit die Darstellung einfach und verständlich bleibt.
DIAGRAMMTYP_AUSWAHL = [
    ("linie", "Linie"),
    ("balken", "Balken"),
    ("kreis", "Kreis"),
]


class Datensatz(models.Model):
    """Dieses Modell speichert die allgemeinen Angaben zu einer Sammlung von Daten. Es hält den Namen, die Beschreibung und die ursprüngliche Quelle an einem gemeinsamen Ort fest."""

    # Der Name bezeichnet den Datensatz eindeutig für die Benutzer und darf höchstens zweihundert Zeichen lang sein. Er wird auch verwendet, wenn ein Datensatz als Text angezeigt wird.
    name = models.CharField(max_length=200)

    # Die Beschreibung bietet Platz für eine längere und verständliche Erklärung zum Inhalt des Datensatzes. Sie ist freiwillig, weil nicht jeder Datensatz zusätzliche Erklärungen benötigt.
    beschreibung = models.TextField(blank=True)

    # Dieser Zeitpunkt wird beim ersten Speichern automatisch eingetragen und danach nicht mehr verändert. Dadurch lässt sich später erkennen, wann der Datensatz im Projekt erstellt wurde.
    erstellt_am = models.DateTimeField(auto_now_add=True)

    # In diesem Feld kann die ursprüngliche Datendatei gespeichert werden, welche von einem Benutzer hochgeladen wurde. Das Feld darf leer sein, wenn die Daten aus einer anderen Quelle stammen oder erst später ergänzt werden.
    quelldatei = models.FileField(upload_to="uploads/", blank=True, null=True)

    # Diese Adresse verweist auf die öffentliche Internetquelle, von welcher die Daten stammen. Sie ist freiwillig und macht besonders bei offenen Daten die Herkunft besser nachvollziehbar.
    quelle_url = models.URLField(blank=True)

    # Dieses Feld speichert das Format der Quelldatei und erlaubt nur CSV oder JSON. Es darf leer bleiben, wenn keine Datei vorhanden ist oder das Format noch nicht bekannt ist.
    dateiformat = models.CharField(
        max_length=10,
        choices=DATEIFORMAT_AUSWAHL,
        blank=True,
    )

    def __str__(self):
        """Diese Methode gibt den Namen zurück, damit der Datensatz im Verwaltungsbereich verständlich angezeigt wird."""
        return self.name

    class Meta:
        """Diese Einstellungen geben dem Modell im Verwaltungsbereich einen richtigen deutschen Namen in der Einzahl und in der Mehrzahl."""

        verbose_name = "Datensatz"
        verbose_name_plural = "Datensätze"


class Datenpunkt(models.Model):
    """Dieses Modell speichert einen einzelnen Wert innerhalb eines Datensatzes. Mehrere Datenpunkte bilden zusammen die Grundlage für ein Diagramm."""

    # Diese Verbindung ordnet den Datenpunkt genau einem Datensatz zu und löscht ihn mit, wenn der zugehörige Datensatz entfernt wird. Über den Namen datenpunkte können alle Werte eines Datensatzes einfach abgefragt werden.
    datensatz = models.ForeignKey(
        Datensatz,
        on_delete=models.CASCADE,
        related_name="datenpunkte",
    )

    # Der X Wert wird als Text gespeichert, weil auf der waagrechten Achse neben Zahlen auch Namen oder andere Kategorien stehen können. Die Länge von zweihundert Zeichen bietet dafür genügend Platz.
    x_wert = models.CharField(max_length=200)

    # Der Y Wert ist eine Zahl mit möglichen Nachkommastellen und stellt die eigentliche messbare Grösse eines Datenpunkts dar. Dieser Wert kann später direkt für Berechnungen und Diagramme verwendet werden.
    y_wert = models.FloatField()

    # Die Kategorie kann ähnliche Datenpunkte als gemeinsame Gruppe kennzeichnen und ist nicht bei jeder Darstellung nötig. Deshalb darf dieses Feld ohne Inhalt gespeichert werden.
    kategorie = models.CharField(max_length=100, blank=True)

    # Diese ganze positive Zahl bestimmt die Position des Datenpunkts innerhalb seines Datensatzes. Neue Datenpunkte erhalten zuerst den Wert null und können später in eine gewünschte Reihenfolge gebracht werden.
    reihenfolge = models.PositiveIntegerField(default=0)

    class Meta:
        """Diese Einstellung sorgt dafür, dass Datenpunkte bei Abfragen immer nach ihrer festgelegten Reihenfolge sortiert werden."""

        ordering = ["reihenfolge"]
        verbose_name = "Datenpunkt"
        verbose_name_plural = "Datenpunkte"


class Diagramm(models.Model):
    """Dieses Modell speichert die Einstellungen für eine grafische Darstellung eines Datensatzes. Es enthält den gewählten Typ, den Titel und die Beschriftungen der beiden Achsen."""

    # Diese Verbindung legt fest, welcher Datensatz im Diagramm dargestellt wird und entfernt das Diagramm beim Löschen dieses Datensatzes ebenfalls. Über den Namen diagramme lassen sich alle Darstellungen eines Datensatzes leicht finden.
    datensatz = models.ForeignKey(
        Datensatz,
        on_delete=models.CASCADE,
        related_name="diagramme",
    )

    # Der Typ bestimmt die Form der Darstellung und erlaubt nur eine Linie, Balken oder einen Kreis. Diese feste Auswahl verhindert ungültige Werte und hält die Bedienung übersichtlich.
    typ = models.CharField(max_length=10, choices=DIAGRAMMTYP_AUSWAHL)

    # Der Titel erklärt kurz, was im Diagramm gezeigt wird, und erscheint gut sichtbar über der Darstellung. Mit höchstens zweihundert Zeichen bleibt er auch bei längeren Bezeichnungen gut verwendbar.
    titel = models.CharField(max_length=200)

    # Diese freiwillige Beschriftung erklärt die Bedeutung der waagrechten Achse. Sie kann leer bleiben, wenn ein Kreisdiagramm verwendet wird oder die Werte bereits ohne Erklärung verständlich sind.
    x_beschriftung = models.CharField(max_length=100, blank=True)

    # Diese freiwillige Beschriftung erklärt die Bedeutung der senkrechten Achse. Sie kann leer bleiben, wenn keine Achse sichtbar ist oder der Titel die dargestellte Grösse bereits deutlich beschreibt.
    y_beschriftung = models.CharField(max_length=100, blank=True)

    # Dieser Wert zeigt an, ob das Programm den Diagrammtyp selbst passend zu den Daten gewählt hat. Der Wert ist zuerst wahr und kann später falsch gesetzt werden, wenn ein Benutzer den Typ selber auswählt.
    automatisch_gewaehlt = models.BooleanField(default=True)

    # Dieser Zeitpunkt wird beim ersten Speichern des Diagramms automatisch gesetzt und bleibt danach unverändert. So kann später nachvollzogen werden, wann eine Darstellung erstellt wurde.
    erstellt_am = models.DateTimeField(auto_now_add=True)

    class Meta:
        """Diese Einstellungen geben dem Modell im Verwaltungsbereich einen richtigen deutschen Namen in der Einzahl und in der Mehrzahl."""

        verbose_name = "Diagramm"
        verbose_name_plural = "Diagramme"
