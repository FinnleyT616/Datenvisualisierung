# Dateiname: forms.py
# Beschreibung: Diese Datei enthält die Formulare für den Datei Upload, die manuelle Dateneingabe und die Anpassung eines Diagramms. Sie prüft die Eingaben und zeigt verständliche deutsche Hinweise und Fehlermeldungen an.

from pathlib import Path

from django import forms


# Diese Auswahl legt fest, welche Trennzeichen bei der manuellen Eingabe verwendet werden können. Der gespeicherte Wert wird später beim Aufteilen der eingegebenen Zeilen gebraucht.
TRENNZEICHEN_AUSWAHL = [
    (",", "Komma"),
    (";", "Semikolon"),
    ("\t", "Tab"),
]

# Diese Auswahl enthält genau die drei Diagrammtypen, welche von der Anwendung dargestellt werden können. Der zuerst erkannte Typ kann im Formular durch einen anderen Eintrag aus dieser Liste ersetzt werden.
DIAGRAMMTYP_AUSWAHL = [
    ("linie", "Linie"),
    ("balken", "Balken"),
    ("kreis", "Kreis"),
]


class DateiUploadFormular(forms.Form):
    """Dieses Formular nimmt eine CSV oder JSON Datei zusammen mit den Angaben zu ihrem Datensatz entgegen. Vor der weiteren Verarbeitung wird geprüft, ob die Datei ein erlaubtes Format und eine passende Grösse hat."""

    # Dieses Feld nimmt die Datei des Benutzers entgegen und zeigt im Dateidialog nur CSV und JSON Dateien als passende Auswahl an. Die zusätzliche Prüfung in der clean Methode bleibt trotzdem nötig, weil die Anzeige im Dateidialog allein keinen sicheren Schutz bietet.
    datei = forms.FileField(
        label="Datei",
        help_text="Erlaubt sind CSV und JSON Dateien mit einer Grösse von höchstens 10 MB.",
        widget=forms.FileInput(
            attrs={
                "class": "form-control",
                "accept": ".csv,.json",
            }
        ),
    )

    # In diesem Feld gibt der Benutzer einen verständlichen Namen für den neuen Datensatz ein. Die maximale Länge entspricht dem Namensfeld des Datensatz Modells und verhindert zu lange Bezeichnungen.
    name = forms.CharField(
        label="Name des Datensatzes",
        max_length=200,
        help_text="Gib einen kurzen und verständlichen Namen für den Datensatz ein.",
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Zum Beispiel Bevölkerungsentwicklung Zürich",
            }
        ),
    )

    # Diese freiwillige Internetadresse nennt die öffentliche Quelle der hochgeladenen Daten. Sie hilft später dabei, die Herkunft der Daten einfach und nachvollziehbar anzugeben.
    quelle_url = forms.URLField(
        label="Open Data Quellenangabe",
        required=False,
        help_text="Füge wenn möglich die Internetadresse der ursprünglichen Open Data Quelle ein.",
        widget=forms.URLInput(
            attrs={
                "class": "form-control",
                "placeholder": "https://example.com/datenquelle",
            }
        ),
    )

    def clean(self):
        """Diese Methode prüft die Endung und die Grösse der hochgeladenen Datei. Fehler werden direkt beim Dateifeld angezeigt, damit der Benutzer sofort weiss, was geändert werden muss."""
        bereinigte_daten = super().clean()
        datei = bereinigte_daten.get("datei")

        # Wenn keine Datei vorhanden ist, hat das Pflichtfeld bereits eine passende Fehlermeldung erstellt. Die weiteren Prüfungen werden dann übersprungen, damit nicht mehrere Meldungen für dasselbe Problem erscheinen.
        if datei is None:
            return bereinigte_daten

        # Die Dateiendung wird in kleine Buchstaben umgewandelt, damit auch Endungen wie CSV oder JSON richtig erkannt werden. Jede andere Endung wird mit einer einfachen deutschen Fehlermeldung abgelehnt.
        dateiendung = Path(datei.name).suffix.lower()
        if dateiendung not in {".csv", ".json"}:
            self.add_error(
                "datei",
                "Dieses Dateiformat wird nicht unterstützt. Bitte lade eine CSV oder JSON Datei hoch.",
            )

        # Die Grösse wird in Byte geprüft und darf zehn Megabyte nicht überschreiten. Dadurch werden sehr grosse Dateien früh abgelehnt, bevor sie unnötig Speicher und Rechenzeit benötigen.
        maximale_dateigroesse = 10 * 1024 * 1024
        if datei.size > maximale_dateigroesse:
            self.add_error(
                "datei",
                "Die Datei ist zu gross. Bitte lade eine Datei mit höchstens 10 MB hoch.",
            )

        return bereinigte_daten


class ManuelleDateneingabeFormular(forms.Form):
    """Dieses Formular erlaubt die Eingabe eines kleinen Datensatzes direkt als Text. Der Benutzer kann das verwendete Trennzeichen wählen und angeben, ob die erste Zeile eine Kopfzeile enthält."""

    # Dieses Feld speichert den Namen, unter welchem die manuell eingegebenen Daten später gefunden werden. Die Länge ist gleich begrenzt wie beim Namen eines hochgeladenen Datensatzes.
    name = forms.CharField(
        label="Name des Datensatzes",
        max_length=200,
        help_text="Gib einen kurzen und verständlichen Namen für den Datensatz ein.",
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Zum Beispiel Monatliche Niederschlagsmenge",
            }
        ),
    )

    # In diesem grossen Textfeld werden die Daten zeilenweise eingegeben und jede Zeile bildet später einen Datenpunkt. Der Platzhalter zeigt ein einfaches Beispiel mit einer Kopfzeile und zwei Datenzeilen.
    daten_text = forms.CharField(
        label="Daten",
        help_text="Trage pro Zeile einen Datenpunkt ein und trenne die Spalten mit dem gewählten Zeichen.",
        widget=forms.Textarea(
            attrs={
                "class": "form-control",
                "rows": 8,
                "placeholder": "Kategorie,Wert\nJanuar,12.5\nFebruar,15.2",
            }
        ),
    )

    # Mit diesem Auswahlfeld legt der Benutzer fest, welches Zeichen die einzelnen Spalten voneinander trennt. Zur Auswahl stehen ein Komma, ein Semikolon und ein Tab Zeichen.
    trennzeichen = forms.ChoiceField(
        label="Trennzeichen",
        choices=TRENNZEICHEN_AUSWAHL,
        help_text="Wähle das Zeichen, welches zwischen den einzelnen Werten steht.",
        widget=forms.Select(attrs={"class": "form-control"}),
    )

    # Dieses Feld zeigt an, ob die erste eingegebene Zeile Namen für die Spalten enthält. Es ist am Anfang ausgewählt, weil viele Datentabellen mit einer Kopfzeile beginnen.
    hat_kopfzeile = forms.BooleanField(
        label="Die erste Zeile ist eine Kopfzeile",
        required=False,
        initial=True,
        help_text="Entferne die Auswahl nur, wenn bereits die erste Zeile echte Daten enthält.",
        widget=forms.CheckboxInput(attrs={"class": "form-control"}),
    )


class DiagrammAnpassungsFormular(forms.Form):
    """Dieses Formular erscheint nach der automatischen Erkennung eines passenden Diagrammtyps. Der Benutzer kann den erkannten Typ übernehmen oder ihn vor dem Erstellen des Diagramms ändern."""

    # Dieses Auswahlfeld zeigt den automatisch erkannten Diagrammtyp als vorausgefüllten Wert an. Der View übergibt diesen Wert beim Erstellen des Formulars und der Benutzer kann zwischen genau drei erlaubten Typen wählen.
    typ = forms.ChoiceField(
        label="Diagrammtyp",
        choices=DIAGRAMMTYP_AUSWAHL,
        help_text="Der vorgeschlagene Typ wurde automatisch erkannt und kann bei Bedarf geändert werden.",
        widget=forms.Select(attrs={"class": "form-control"}),
    )

    # In diesem Feld wird der sichtbare Titel des Diagramms festgelegt. Ein klarer Titel hilft den Benutzern dabei, den dargestellten Inhalt schnell zu verstehen.
    titel = forms.CharField(
        label="Titel des Diagramms",
        max_length=200,
        help_text="Gib einen passenden Titel für die Darstellung ein.",
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Zum Beispiel Entwicklung von 2020 bis 2025",
            }
        ),
    )
