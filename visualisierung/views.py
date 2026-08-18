# Dateiname: views.py
# Beschreibung: Diese Datei enthält die Ansichten und die Geschäftslogik der Visualisierungs App. Sie verarbeitet Datensätze, erstellt Diagramme und liefert die passenden Inhalte an die Vorlagen weiter.

from pathlib import Path

import pandas as pd
from django.contrib import messages
from django.db import transaction
from django.http import FileResponse
from django.shortcuts import get_object_or_404, redirect, render

from .diagramm_ersteller import DiagrammErsteller
from .forms import (
    DateiUploadFormular,
    DiagrammAnpassungsFormular,
    ManuelleDateneingabeFormular,
)
from .models import Datensatz, Diagramm
from .statistik import kennzahlen_berechnen
from .utils import (
    csv_einlesen,
    dataframe_zu_datenpunkte,
    datensatz_zu_dataframe,
    daten_validieren,
    datentyp_erkennen,
    json_einlesen,
    text_zu_dataframe,
)


def _spalten_fuer_datenpunkte_bestimmen(dataframe):
    """Bestimmt aus einer geprüften Tabelle die X Spalte, die erste passende numerische Y Spalte und eine mögliche Kategoriespalte. Die einfache Auswahl folgt der üblichen Tabellenstruktur und liefert verständliche Fehler, wenn keine Wertespalte gefunden wird."""

    # Die erste Spalte wird als X Spalte verwendet, weil dort bei üblichen Datensätzen die Zeit, Reihenfolge oder Bezeichnung steht. Rechts davon wird nach der ersten Spalte gesucht, deren vorhandene Werte vollständig in Zahlen umgewandelt werden können.
    x_spalte = dataframe.columns[0]
    y_spalte = None
    for spaltenname in dataframe.columns[1:]:
        vorhandene_werte = dataframe[spaltenname].dropna()
        numerische_werte = pd.to_numeric(
            vorhandene_werte,
            errors="coerce",
        )
        if not vorhandene_werte.empty and numerische_werte.notna().all():
            y_spalte = spaltenname
            break

    # Ohne numerische Spalte rechts von der X Spalte könnten keine gültigen Y Werte gespeichert werden. Der Benutzer erhält deshalb eine genaue Meldung und kann die Datei oder Texteingabe verbessern.
    if y_spalte is None:
        raise ValueError(
            "Es wurde keine numerische Wertespalte rechts von der ersten Spalte gefunden."
        )

    # Die ausgewählte Y Spalte wird vollständig in Zahlen umgewandelt, damit später keine Textwerte in einem Float Feld gespeichert werden. Ungültige oder leere Werte werden dadurch früh erkannt.
    dataframe[y_spalte] = pd.to_numeric(
        dataframe[y_spalte],
        errors="raise",
    )

    # Eine weitere Textspalte kann als Kategorie für mehrere Linien oder gruppierte Balken verwendet werden. Numerische Zusatzspalten werden nicht automatisch als Kategorie gewählt, weil Zahlen meistens weitere Messwerte darstellen.
    kategorie_spalte = None
    for spaltenname in dataframe.columns[1:]:
        if spaltenname == y_spalte:
            continue
        vorhandene_werte = dataframe[spaltenname].dropna()
        numerische_werte = pd.to_numeric(
            vorhandene_werte,
            errors="coerce",
        )
        if vorhandene_werte.empty or not numerische_werte.notna().all():
            kategorie_spalte = spaltenname
            break

    return x_spalte, y_spalte, kategorie_spalte


def _dataframe_als_datensatz_speichern(
    dataframe,
    name,
    quelle_url="",
    dateiformat="",
    quelldatei=None,
):
    """Speichert eine geprüfte Pandas Tabelle gemeinsam mit ihrem Datensatz und allen Datenpunkten. Eine Datenbanktransaktion stellt sicher, dass bei einem Fehler weder ein unvollständiger Datensatz noch einzelne Datenpunkte zurückbleiben."""

    # Die Spalten werden vor dem Erstellen des Datensatzes bestimmt. Dadurch wird eine ungeeignete Tabelle abgelehnt, bevor eine Datei oder ein unvollständiger Eintrag in der Datenbank gespeichert wird.
    x_spalte, y_spalte, kategorie_spalte = _spalten_fuer_datenpunkte_bestimmen(
        dataframe
    )

    # Innerhalb der Transaktion werden der Datensatz und seine Datenpunkte als eine zusammengehörende Änderung behandelt. Schlägt ein Schritt fehl, macht Django alle bisherigen Datenbankänderungen dieses Blocks rückgängig.
    with transaction.atomic():
        datensatz = Datensatz.objects.create(
            name=name,
            quelle_url=quelle_url,
            dateiformat=dateiformat,
            quelldatei=quelldatei,
        )
        dataframe_zu_datenpunkte(
            datensatz,
            dataframe,
            x_spalte,
            y_spalte,
            kategorie_spalte,
        )

    return datensatz


def startseite(request):
    """Zeigt eine kurze und einfache Erklärung zu Open Data sowie die fünf zuletzt erstellten Datensätze. Neue Einträge stehen am Anfang, damit die zuletzt bearbeiteten Daten schnell wiedergefunden werden."""

    # Die Datenbankabfrage sortiert nach dem Erstellungszeitpunkt und begrenzt das Ergebnis direkt auf fünf Einträge. Dadurch werden keine unnötigen älteren Datensätze geladen.
    datensaetze = Datensatz.objects.order_by("-erstellt_am")[:5]
    kontext = {
        "datensaetze": datensaetze,
        "open_data_erklaerung": "Open Data sind Daten, die öffentlich zugänglich sind und von allen Menschen verwendet, untersucht und weitergegeben werden dürfen.",
    }
    return render(request, "visualisierung/startseite.html", kontext)


def datensatz_hochladen(request):
    """Zeigt zwei Formulare für einen Datei Upload oder eine manuelle Dateneingabe und verarbeitet beide Wege. Nach einer erfolgreichen Prüfung werden der Datensatz und seine Datenpunkte gespeichert und der Benutzer gelangt zur Detailansicht."""

    # Beide Formulare werden bei jeder Anfrage bereitgestellt, damit die Vorlage sie in getrennten Tabs anzeigen kann. Das Feld formular_typ zeigt bei einer Anfrage mit POST, welcher Tab abgeschickt wurde.
    formular_typ = request.POST.get("formular_typ", "datei")
    datei_formular = DateiUploadFormular()
    manuell_formular = ManuelleDateneingabeFormular()

    if request.method == "POST" and formular_typ == "datei":
        datei_formular = DateiUploadFormular(request.POST, request.FILES)
        if datei_formular.is_valid():
            hochgeladene_datei = datei_formular.cleaned_data["datei"]
            dateiendung = Path(hochgeladene_datei.name).suffix.lower()

            try:
                # Die bereits geprüfte Endung entscheidet, welche Einlesefunktion verwendet wird. Nach dem Lesen wird der Dateizeiger zurückgesetzt, damit Django beim Speichern wieder den vollständigen Dateiinhalt erhält.
                if dateiendung == ".csv":
                    dataframe = csv_einlesen(hochgeladene_datei)
                    dateiformat = "csv"
                else:
                    dataframe = json_einlesen(hochgeladene_datei)
                    dateiformat = "json"
                hochgeladene_datei.seek(0)

                ist_gueltig, fehlermeldung = daten_validieren(dataframe)
                if not ist_gueltig:
                    raise ValueError(fehlermeldung)

                datensatz = _dataframe_als_datensatz_speichern(
                    dataframe=dataframe,
                    name=datei_formular.cleaned_data["name"],
                    quelle_url=datei_formular.cleaned_data["quelle_url"],
                    dateiformat=dateiformat,
                    quelldatei=hochgeladene_datei,
                )
                messages.success(
                    request,
                    "Der Datensatz wurde erfolgreich hochgeladen und gespeichert.",
                )
                return redirect(
                    "visualisierung:datensatz_detail",
                    datensatz_id=datensatz.pk,
                )
            except (OSError, UnicodeError, ValueError, TypeError) as fehler:
                # Fehler aus dem Einlesen, der Prüfung oder der Spaltenauswahl werden oberhalb des Formulars angezeigt. Der Benutzer bleibt auf derselben Seite und kann eine andere Datei auswählen.
                messages.error(request, str(fehler))
        else:
            messages.error(
                request,
                "Die Datei konnte nicht verarbeitet werden. Bitte prüfe die markierten Felder.",
            )

    elif request.method == "POST" and formular_typ == "manuell":
        manuell_formular = ManuelleDateneingabeFormular(request.POST)
        if manuell_formular.is_valid():
            try:
                # Der eingegebene Text wird mit den gewählten Einstellungen in eine Tabelle umgewandelt. Manuell erstellte Datensätze besitzen keine Quelldatei und deshalb auch kein festes Dateiformat.
                dataframe = text_zu_dataframe(
                    manuell_formular.cleaned_data["daten_text"],
                    manuell_formular.cleaned_data["trennzeichen"],
                    manuell_formular.cleaned_data["hat_kopfzeile"],
                )
                ist_gueltig, fehlermeldung = daten_validieren(dataframe)
                if not ist_gueltig:
                    raise ValueError(fehlermeldung)

                datensatz = _dataframe_als_datensatz_speichern(
                    dataframe=dataframe,
                    name=manuell_formular.cleaned_data["name"],
                )
                messages.success(
                    request,
                    "Der manuell eingegebene Datensatz wurde erfolgreich gespeichert.",
                )
                return redirect(
                    "visualisierung:datensatz_detail",
                    datensatz_id=datensatz.pk,
                )
            except (OSError, UnicodeError, ValueError, TypeError) as fehler:
                messages.error(request, str(fehler))
        else:
            messages.error(
                request,
                "Die Eingabe konnte nicht verarbeitet werden. Bitte prüfe die markierten Felder.",
            )

    kontext = {
        "datei_formular": datei_formular,
        "manuell_formular": manuell_formular,
        "aktiver_tab": formular_typ,
    }
    return render(request, "visualisierung/datensatz_hochladen.html", kontext)


def datensatz_detail(request, datensatz_id):
    """Zeigt die Angaben eines Datensatzes und höchstens fünfzig seiner Datenpunkte. Die Vorlage kann zusätzlich die Quellenadresse als Link und einen Knopf für die automatische Diagrammanalyse anzeigen."""

    # get_object_or_404 liefert eine normale Fehlerseite mit dem Status 404, wenn die angegebene Nummer nicht existiert. So entsteht kein unverständlicher Datenbankfehler.
    datensatz = get_object_or_404(Datensatz, pk=datensatz_id)
    datenpunkte = datensatz.datenpunkte.all()[:50]
    kontext = {
        "datensatz": datensatz,
        "datenpunkte": datenpunkte,
    }
    return render(request, "visualisierung/datensatz_detail.html", kontext)


def diagramm_erstellen(request, datensatz_id):
    """Analysiert die Daten automatisch und zeigt den erkannten Typ mit einer verständlichen Begründung an. Der Benutzer kann den Vorschlag übernehmen oder ändern, bevor das Diagramm gespeichert und für die Anzeige vorbereitet wird."""

    datensatz = get_object_or_404(Datensatz, pk=datensatz_id)
    dataframe = datensatz_zu_dataframe(datensatz)
    erkennung = datentyp_erkennen(dataframe)

    if request.method == "POST":
        formular = DiagrammAnpassungsFormular(request.POST)
        if formular.is_valid():
            gewaehlter_typ = formular.cleaned_data["typ"]
            automatisch_gewaehlt = gewaehlter_typ == erkennung["typ"]

            try:
                # Das Diagramm wird zuerst in der Datenbank gespeichert und danach einmal als interaktiver HTML Code erstellt. Dadurch werden ungültige Daten erkannt, bevor der Benutzer zur Anzeige weitergeleitet wird.
                with transaction.atomic():
                    diagramm = Diagramm.objects.create(
                        datensatz=datensatz,
                        typ=gewaehlter_typ,
                        titel=formular.cleaned_data["titel"],
                        automatisch_gewaehlt=automatisch_gewaehlt,
                    )
                    DiagrammErsteller(
                        datensatz,
                        diagramm,
                    ).erstellen_interaktiv()

                messages.success(
                    request,
                    "Das Diagramm wurde erfolgreich erstellt.",
                )
                return redirect(
                    "visualisierung:diagramm_anzeige",
                    diagramm_id=diagramm.pk,
                )
            except (OSError, ValueError, TypeError) as fehler:
                messages.error(
                    request,
                    f"Das Diagramm konnte nicht erstellt werden. {fehler}",
                )
        else:
            messages.error(
                request,
                "Bitte prüfe den ausgewählten Diagrammtyp und den Titel.",
            )
    else:
        # Beim ersten Öffnen wird das Formular mit dem erkannten Typ und einem einfachen Titel vorausgefüllt. Der Benutzer sieht den Vorschlag sofort und kann ihn trotzdem ändern.
        formular = DiagrammAnpassungsFormular(
            initial={
                "typ": erkennung["typ"],
                "titel": datensatz.name,
            }
        )

    kontext = {
        "datensatz": datensatz,
        "erkennung": erkennung,
        "formular": formular,
    }
    return render(request, "visualisierung/diagramm_erstellen.html", kontext)


def diagramm_anzeige(request, diagramm_id):
    """Zeigt ein gespeichertes Diagramm als interaktive Plotly Darstellung. Zusätzlich werden die Auswahlart, einfache statistische Kennzahlen und die Möglichkeiten für einen PNG oder PDF Export an die Vorlage übergeben."""

    diagramm = get_object_or_404(
        Diagramm.objects.select_related("datensatz"),
        pk=diagramm_id,
    )

    try:
        # Der HTML Code enthält das interaktive div Element für die Vorlage. Die Kennzahlen werden direkt aus denselben gespeicherten Datenpunkten berechnet, welche auch im Diagramm erscheinen.
        diagramm_html = DiagrammErsteller(
            diagramm.datensatz,
            diagramm,
        ).erstellen_interaktiv()
        kennzahlen = kennzahlen_berechnen(
            diagramm.datensatz.datenpunkte.all()
        )
    except (OSError, ValueError, TypeError) as fehler:
        messages.error(
            request,
            f"Das Diagramm konnte nicht angezeigt werden. {fehler}",
        )
        return redirect(
            "visualisierung:datensatz_detail",
            datensatz_id=diagramm.datensatz.pk,
        )

    kontext = {
        "diagramm": diagramm,
        "diagramm_html": diagramm_html,
        "kennzahlen": kennzahlen,
        "automatisch_gewaehlt": diagramm.automatisch_gewaehlt,
    }
    return render(request, "visualisierung/diagramm_anzeige.html", kontext)


def diagramm_exportieren(request, diagramm_id, format):
    """Erstellt ein gespeichertes Diagramm als statische PNG oder PDF Datei und liefert sie als Download aus. Das passende Inhaltsformat wird gesetzt, damit der Browser die Datei richtig behandelt."""

    diagramm = get_object_or_404(
        Diagramm.objects.select_related("datensatz"),
        pk=diagramm_id,
    )
    dateiformat = format.lower()

    # Nur die beiden vorgesehenen Exportformate werden akzeptiert. Bei einer anderen Adresse gelangt der Benutzer mit einer deutschen Fehlermeldung zurück zum Diagramm.
    if dateiformat not in {"png", "pdf"}:
        messages.error(
            request,
            "Dieses Exportformat wird nicht unterstützt. Erlaubt sind nur PNG und PDF.",
        )
        return redirect(
            "visualisierung:diagramm_anzeige",
            diagramm_id=diagramm.pk,
        )

    try:
        dateipfad = DiagrammErsteller(
            diagramm.datensatz,
            diagramm,
        ).erstellen_statisch(dateiformat)
        inhaltstypen = {
            "png": "image/png",
            "pdf": "application/pdf",
        }

        # FileResponse liest die Datei stückweise und hält dadurch auch bei grösseren Exporten den Speicherverbrauch klein. as_attachment sorgt dafür, dass der Browser einen Download mit einem verständlichen Dateinamen anbietet.
        return FileResponse(
            open(dateipfad, "rb"),
            content_type=inhaltstypen[dateiformat],
            as_attachment=True,
            filename=Path(dateipfad).name,
        )
    except (OSError, ValueError, TypeError) as fehler:
        messages.error(
            request,
            f"Das Diagramm konnte nicht exportiert werden. {fehler}",
        )
        return redirect(
            "visualisierung:diagramm_anzeige",
            diagramm_id=diagramm.pk,
        )


def verlauf(request):
    """Zeigt alle gespeicherten Datensätze und Diagramme, jeweils mit den neuesten Einträgen zuerst. Die getrennten Listen können in der Vorlage gemeinsam als übersichtlicher Verlauf dargestellt werden."""

    # Beide Abfragen verwenden den Erstellungszeitpunkt für eine absteigende Sortierung. select_related lädt bei den Diagrammen den zugehörigen Datensatz direkt mit und verhindert dadurch unnötige einzelne Datenbankabfragen in der Vorlage.
    datensaetze = Datensatz.objects.order_by("-erstellt_am")
    diagramme = Diagramm.objects.select_related("datensatz").order_by(
        "-erstellt_am"
    )
    kontext = {
        "datensaetze": datensaetze,
        "diagramme": diagramme,
    }
    return render(request, "visualisierung/verlauf.html", kontext)
