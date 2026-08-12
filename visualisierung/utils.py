# Dateiname: utils.py
# Beschreibung: Diese Datei enthält Hilfsfunktionen zum Einlesen, Prüfen und Umwandeln von Daten. Sie verbindet Tabellen aus Pandas mit den Datenpunkten in der Django Datenbank.

import json
from io import BytesIO, StringIO
from pathlib import Path

import pandas as pd

from .models import Datenpunkt


def csv_einlesen(dateipfad_oder_datei, trennzeichen=None):
    """Liest eine CSV Datei aus einem Pfad oder einem geöffneten Dateiobjekt ein und gibt eine Pandas Tabelle zurück. Wenn kein Trennzeichen angegeben wurde, werden Komma, Semikolon und Tab ausprobiert und die sinnvollste Tabelle mit den meisten erkannten Spalten wird verwendet. Fehler beim Lesen werden abgefangen und als verständliche deutsche Meldung weitergegeben."""

    try:
        # Ein geöffnetes Dateiobjekt wird einmal vollständig gelesen und danach für jeden Versuch neu bereitgestellt. Das ist wichtig, weil der erste Leseversuch den Zeiger sonst ans Ende verschiebt und die nächsten Trennzeichen keine Daten mehr erhalten würden.
        if hasattr(dateipfad_oder_datei, "read"):
            dateipfad_oder_datei.seek(0)
            dateiinhalt = dateipfad_oder_datei.read()

            # Binäre Inhalte benötigen einen Bytes Puffer und normale Texte benötigen einen String Puffer. Beide Puffer verhalten sich für Pandas wie eine geöffnete Datei und können beliebig oft neu erstellt werden.
            if isinstance(dateiinhalt, bytes):
                quelle_erstellen = lambda: BytesIO(dateiinhalt)
            else:
                quelle_erstellen = lambda: StringIO(dateiinhalt)
        else:
            # Bei einem Dateipfad kann Pandas die Datei für jeden Versuch selbst erneut öffnen. Die kleine Funktion liefert deshalb immer wieder denselben Pfad zurück.
            quelle_erstellen = lambda: dateipfad_oder_datei

        # Wenn der Benutzer ein Trennzeichen vorgibt, wird genau dieses Zeichen verwendet. So bleibt die Verarbeitung vorhersehbar, wenn das Format der Datei bereits bekannt ist.
        if trennzeichen is not None:
            return pd.read_csv(quelle_erstellen(), sep=trennzeichen)

        beste_tabelle = None
        groesste_spaltenzahl = 0
        letzter_fehler = None

        # Jedes erlaubte Trennzeichen wird einzeln ausprobiert und die Anzahl der erkannten Spalten wird verglichen. Das richtige Zeichen erzeugt normalerweise mehr Spalten als ein Zeichen, das in der Datei gar nicht vorkommt.
        for moegliches_trennzeichen in [",", ";", "\t"]:
            try:
                tabelle = pd.read_csv(
                    quelle_erstellen(),
                    sep=moegliches_trennzeichen,
                )
            except (OSError, UnicodeError, ValueError) as fehler:
                letzter_fehler = fehler
                continue

            if len(tabelle.columns) > groesste_spaltenzahl:
                beste_tabelle = tabelle
                groesste_spaltenzahl = len(tabelle.columns)

        # Wenn kein einziger Versuch eine Tabelle ergeben hat, wird eine klare Fehlermeldung ausgegeben. Der ursprüngliche Fehler bleibt als Ursache erhalten und hilft bei einer späteren technischen Untersuchung.
        if beste_tabelle is None:
            raise ValueError(
                "Die CSV Datei konnte nicht gelesen werden. Prüfe den Inhalt und die Zeichenkodierung der Datei."
            ) from letzter_fehler

        return beste_tabelle
    except (OSError, UnicodeError, ValueError, TypeError) as fehler:
        # Bereits verständliche eigene Fehlermeldungen werden unverändert weitergegeben. Alle anderen Fehler werden in eine einfache deutsche Meldung verpackt, damit im Formular keine schwer verständliche technische Ausgabe erscheint.
        if isinstance(fehler, ValueError) and str(fehler).startswith("Die CSV Datei konnte"):
            raise
        raise ValueError(
            "Die CSV Datei konnte nicht gelesen werden. Bitte prüfe, ob die Datei gültige Tabellendaten enthält."
        ) from fehler


def json_einlesen(dateipfad_oder_datei):
    """Liest eine JSON Datei aus einem Pfad oder einem geöffneten Dateiobjekt ein und gibt eine Pandas Tabelle zurück. Flache Listen werden direkt in eine Tabelle umgewandelt und einfach verschachtelte Objekte werden mit json_normalize aufgelöst. Ungültige Inhalte führen zu einer verständlichen deutschen Fehlermeldung."""

    try:
        # Ein geöffnetes Dateiobjekt wird an den Anfang gesetzt und vollständig gelesen. Bei einem Pfad übernimmt Python das sichere Öffnen und schliesst die Datei nach dem Lesen automatisch wieder.
        if hasattr(dateipfad_oder_datei, "read"):
            dateipfad_oder_datei.seek(0)
            dateiinhalt = dateipfad_oder_datei.read()
        else:
            dateiinhalt = Path(dateipfad_oder_datei).read_bytes()

        # Binäre Inhalte werden als Text mit der üblichen UTF 8 Zeichenkodierung gelesen. Danach wandelt das JSON Modul den Text in normale Python Listen und Wörterbücher um.
        if isinstance(dateiinhalt, bytes):
            dateiinhalt = dateiinhalt.decode("utf-8-sig")
        json_daten = json.loads(dateiinhalt)

        # Eine Liste mit flachen Objekten kann direkt als Tabelle aufgebaut werden. Sobald ein Wert selbst wieder ein Objekt oder eine Liste enthält, löst json_normalize die einfache Verschachtelung in verständliche Spalten auf.
        if isinstance(json_daten, list):
            ist_verschachtelt = any(
                isinstance(wert, (dict, list))
                for eintrag in json_daten
                if isinstance(eintrag, dict)
                for wert in eintrag.values()
            )
            if ist_verschachtelt:
                return pd.json_normalize(json_daten)
            return pd.DataFrame(json_daten)

        # Bei einem einzelnen Objekt wird zuerst geprüft, ob es genau eine Liste mit Datensätzen enthält. Dieses häufige Format wird direkt entpackt, damit jeder Eintrag eine eigene Tabellenzeile erhält.
        if isinstance(json_daten, dict):
            listenwerte = [
                wert
                for wert in json_daten.values()
                if isinstance(wert, list)
            ]
            if len(listenwerte) == 1 and all(
                isinstance(eintrag, dict) for eintrag in listenwerte[0]
            ):
                return pd.json_normalize(listenwerte[0])

            # Andere einzelne oder einfach verschachtelte Objekte werden mit json_normalize in eine Tabellenzeile mit passenden Spalten umgewandelt.
            return pd.json_normalize(json_daten)

        raise ValueError(
            "Die JSON Datei muss eine Liste oder ein Objekt mit Daten enthalten."
        )
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError, TypeError) as fehler:
        # Eine bereits verständliche Meldung zur Grundstruktur bleibt erhalten. Alle anderen Fehler erhalten eine gemeinsame Meldung, welche dem Benutzer das Problem ohne technische Einzelheiten erklärt.
        if isinstance(fehler, ValueError) and str(fehler).startswith("Die JSON Datei muss"):
            raise
        raise ValueError(
            "Die JSON Datei konnte nicht gelesen werden. Bitte prüfe, ob sie gültige JSON Daten enthält."
        ) from fehler


def text_zu_dataframe(text, trennzeichen=",", hat_kopfzeile=True):
    """Wandelt manuell eingegebenen Text mit StringIO in eine Pandas Tabelle um. Das gewählte Trennzeichen teilt die Spalten auf und die erste Zeile kann entweder als Kopfzeile oder als normale Datenzeile behandelt werden. Fehler werden als einfache deutsche Meldung ausgegeben."""

    try:
        # StringIO lässt den eingegebenen Text für Pandas wie eine normale Datei aussehen. Der Wert null verwendet die erste Zeile als Spaltennamen und der Wert None lässt Pandas einfache Nummern als Spaltennamen erstellen.
        kopfzeile = 0 if hat_kopfzeile else None
        textpuffer = StringIO(text)
        return pd.read_csv(
            textpuffer,
            sep=trennzeichen,
            header=kopfzeile,
        )
    except (UnicodeError, ValueError, TypeError) as fehler:
        # Fehlerhafte Zeilen oder ein ungeeignetes Trennzeichen werden mit einer verständlichen Meldung weitergegeben. Dadurch kann der Benutzer seine Eingabe direkt verbessern.
        raise ValueError(
            "Die eingegebenen Daten konnten nicht gelesen werden. Bitte prüfe die Zeilen und das gewählte Trennzeichen."
        ) from fehler


def dataframe_zu_datenpunkte(
    datensatz,
    dataframe,
    x_spalte,
    y_spalte,
    kategorie_spalte=None,
):
    """Wandelt jede Zeile einer Pandas Tabelle in einen Datenpunkt für den angegebenen Datensatz um. Die X Spalte darf Text enthalten, während die Y Spalte in Zahlen umgewandelt wird. Alle vorbereiteten Objekte werden gemeinsam mit bulk_create gespeichert und erhalten ihre Reihenfolge automatisch."""

    # Vor dem Erstellen der Objekte wird kontrolliert, ob alle angegebenen Spalten wirklich vorhanden sind. Eine frühe Prüfung verhindert, dass erst mitten in der Verarbeitung eine schwer verständliche Fehlermeldung entsteht.
    benoetigte_spalten = [x_spalte, y_spalte]
    if kategorie_spalte is not None:
        benoetigte_spalten.append(kategorie_spalte)
    fehlende_spalten = [
        spalte for spalte in benoetigte_spalten if spalte not in dataframe.columns
    ]
    if fehlende_spalten:
        raise ValueError(
            "Diese Spalten wurden in den Daten nicht gefunden: "
            + ", ".join(str(spalte) for spalte in fehlende_spalten)
            + "."
        )

    datenpunkte = []

    # Jede Tabellenzeile wird zuerst vollständig in ein Datenpunkt Objekt umgewandelt, ohne sie sofort in der Datenbank zu speichern. Dadurch kann ein fehlerhafter Zahlenwert erkannt werden, bevor ein Teil der Daten bereits gespeichert wurde.
    for reihenfolge, (_, zeile) in enumerate(dataframe.iterrows()):
        try:
            y_wert = float(zeile[y_spalte])
        except (TypeError, ValueError) as fehler:
            raise ValueError(
                f"Der Y Wert in Zeile {reihenfolge + 1} ist keine gültige Zahl."
            ) from fehler

        # Ein fehlender X Wert wird als leerer Text gespeichert und normale Werte werden immer in Text umgewandelt. Das passt zum Modell, weil eine waagrechte Achse sowohl Zahlen als auch Kategorien enthalten darf.
        x_rohwert = zeile[x_spalte]
        x_wert = "" if pd.isna(x_rohwert) else str(x_rohwert)

        # Ohne angegebene Kategoriespalte bleibt die Kategorie leer. Auch leere Werte aus einer vorhandenen Spalte werden nicht als Text nan gespeichert, sondern sauber durch einen leeren Text ersetzt.
        kategorie = ""
        if kategorie_spalte is not None:
            kategorie_rohwert = zeile[kategorie_spalte]
            if not pd.isna(kategorie_rohwert):
                kategorie = str(kategorie_rohwert)

        datenpunkte.append(
            Datenpunkt(
                datensatz=datensatz,
                x_wert=x_wert,
                y_wert=y_wert,
                kategorie=kategorie,
                reihenfolge=reihenfolge,
            )
        )

    # bulk_create speichert alle vorbereiteten Datenpunkte mit einer einzigen Datenbankabfrage. Das ist bei grösseren Tabellen deutlich schneller als jedes Objekt einzeln zu speichern.
    return Datenpunkt.objects.bulk_create(datenpunkte)


def datensatz_zu_dataframe(datensatz):
    """Lädt alle Datenpunkte des angegebenen Datensatzes aus der Datenbank und gibt sie als Pandas Tabelle zurück. Die Werte erscheinen dank der Modelleinstellung in ihrer gespeicherten Reihenfolge und können danach direkt für Berechnungen oder Diagramme verwendet werden."""

    # values beschränkt die Datenbankabfrage auf die Felder, welche für eine Tabelle benötigt werden. Die Umwandlung in eine Liste führt die Abfrage einmal aus und Pandas baut daraus die fertige Tabelle auf.
    datenpunkte = list(
        datensatz.datenpunkte.values(
            "x_wert",
            "y_wert",
            "kategorie",
            "reihenfolge",
        )
    )
    return pd.DataFrame(
        datenpunkte,
        columns=["x_wert", "y_wert", "kategorie", "reihenfolge"],
    )


def daten_validieren(dataframe):
    """Prüft, ob eine Pandas Tabelle mindestens zwei Spalten und mindestens einen verwendbaren Zahlenwert enthält. Die Funktion gibt immer ein Tupel mit einem Wahrheitswert und einer deutschen Fehlermeldung zurück. Bei gültigen Daten bleibt die Fehlermeldung leer."""

    # Eine gültige Pandas Tabelle wird vorausgesetzt, weil nur sie die benötigten Spalten und Umwandlungsfunktionen bereitstellt. Diese Prüfung liefert bei einem falschen Wert eine klare Meldung statt eines technischen Fehlers.
    if not isinstance(dataframe, pd.DataFrame):
        return False, "Die übergebenen Daten sind keine gültige Tabelle."

    # Für ein einfaches Diagramm werden mindestens zwei Spalten benötigt, weil eine Spalte die Beschriftung und eine weitere Spalte die Werte enthalten soll.
    if len(dataframe.columns) < 2:
        return False, "Die Daten müssen mindestens zwei Spalten enthalten."

    # Jede Spalte wird versuchsweise in Zahlen umgewandelt und unpassende Inhalte werden dabei zu leeren Werten. Sobald mindestens ein echter Zahlenwert übrig bleibt, können die Daten grundsätzlich für ein Diagramm verwendet werden.
    numerische_daten_vorhanden = any(
        pd.to_numeric(dataframe[spalte], errors="coerce").notna().any()
        for spalte in dataframe.columns
    )
    if not numerische_daten_vorhanden:
        return False, "Die Daten enthalten keine numerischen Werte für ein Diagramm."

    return True, ""


def datentyp_erkennen(dataframe):
    """Analysiert die Struktur einer Pandas Tabelle und wählt automatisch einen passenden Diagrammtyp aus. Die Entscheidung ist auf die drei Typen Linie, Balken und Kreis beschränkt und wird zusammen mit einer einfachen deutschen Begründung zurückgegeben. Dabei werden Zeitreihen, Kategorien und mögliche Anteilswerte in einer festen und nachvollziehbaren Reihenfolge untersucht."""

    # Am Anfang wird geprüft, ob wirklich eine Pandas Tabelle mit mindestens zwei Spalten und mindestens einer Zeile vorliegt. Ohne eine X Spalte, eine weitere Wertespalte und echte Daten ist keine sichere Erkennung möglich, deshalb wird in diesem Fall der vorgesehene Balken Fallback mit einer ehrlichen Begründung verwendet.
    if (
        not isinstance(dataframe, pd.DataFrame)
        or len(dataframe.columns) < 2
        or dataframe.empty
    ):
        return {
            "typ": "balken",
            "begruendung": "Die Daten enthalten zu wenige Spalten oder Zeilen für eine sichere automatische Erkennung. Deshalb wird als einfache und gut lesbare Darstellung ein Balkendiagramm verwendet.",
        }

    # Jede Spalte wird einzeln untersucht, damit die Funktion zwischen Zahlen und Text unterscheiden kann. Eine Spalte gilt als numerisch, wenn alle vorhandenen Werte ohne Fehler in Zahlen umgewandelt werden können und wenigstens ein echter Wert vorhanden ist.
    numerische_spalten = []
    text_spalten = []
    umgewandelte_spalten = {}
    for spaltenname in dataframe.columns:
        vorhandene_werte = dataframe[spaltenname].dropna()
        umgewandelte_werte = pd.to_numeric(
            vorhandene_werte,
            errors="coerce",
        )
        ist_numerisch = (
            not vorhandene_werte.empty
            and umgewandelte_werte.notna().all()
        )

        if ist_numerisch:
            numerische_spalten.append(spaltenname)
            umgewandelte_spalten[spaltenname] = pd.to_numeric(
                dataframe[spaltenname],
                errors="coerce",
            )
        else:
            text_spalten.append(spaltenname)

    # Die erste Spalte wird immer als X Spalte betrachtet, weil sie bei üblichen Tabellen die Reihenfolge, Zeit oder Kategorien enthält. Als Y Spalte wird bevorzugt die erste numerische Spalte rechts davon verwendet, damit die dargestellten Werte nicht mit einer numerischen X Achse verwechselt werden.
    x_spalte = dataframe.columns[0]
    numerische_y_spalten = [
        spaltenname
        for spaltenname in dataframe.columns[1:]
        if spaltenname in numerische_spalten
    ]

    # Falls rechts von der X Spalte keine vollständige Zahlenspalte erkannt wurde, fehlt eine verlässliche Grundlage für eine Linie oder einen Kreis. Ein Balkendiagramm ist dann der verständlichste Fallback, weil es auch bei gemischten oder noch nicht ganz sauberen Daten am leichtesten zu lesen ist.
    if not numerische_y_spalten:
        return {
            "typ": "balken",
            "begruendung": "Neben der ersten Spalte wurde keine vollständig numerische Wertespalte erkannt. Deshalb wird ein Balkendiagramm verwendet, weil es auch für gemischte Kategorien und Werte gut verständlich ist.",
        }

    y_spalte = numerische_y_spalten[0]
    y_werte = umgewandelte_spalten[y_spalte].dropna()

    # Nun wird die erste Spalte auf eine mögliche Zeitreihe geprüft. Dafür muss sie vollständig aus Zahlen bestehen, mindestens zwei verschiedene Werte enthalten und in aufsteigender Reihenfolge stehen, denn ein Verlauf benötigt eine erkennbare Richtung von früher nach später.
    x_ist_numerisch = x_spalte in numerische_spalten
    x_werte = None
    x_ist_aufsteigend = False
    if x_ist_numerisch:
        x_werte = umgewandelte_spalten[x_spalte].dropna()
        x_ist_aufsteigend = (
            len(x_werte) >= 2
            and x_werte.is_unique
            and x_werte.is_monotonic_increasing
        )

    # Jahreszahlen werden daran erkannt, dass sie ganze Zahlen in einem sinnvollen Bereich sind und aufsteigend angeordnet wurden. Kleine Lücken zwischen Jahren sind erlaubt, weil echte Datensätze nicht zwingend für jedes einzelne Jahr einen Wert enthalten.
    x_enthaelt_jahreszahlen = False
    if x_ist_aufsteigend:
        x_enthaelt_jahreszahlen = (
            x_werte.between(1000, 2100).all()
            and (x_werte % 1 == 0).all()
        )

    # Fortlaufende Zahlen werden etwas strenger als Jahreszahlen geprüft. Die Abstände zwischen den sortierten Werten müssen gleich gross und positiv sein, damit die Punkte tatsächlich eine gleichmässige Reihenfolge und nicht nur beliebige Nummern darstellen.
    x_enthaelt_fortlaufende_zahlen = False
    if x_ist_aufsteigend:
        abstaende = x_werte.diff().dropna()
        x_enthaelt_fortlaufende_zahlen = (
            not abstaende.empty
            and (abstaende > 0).all()
            and abstaende.nunique() == 1
        )

    # Eine erkannte Zeitreihe erhält Vorrang vor einem Kreisdiagramm, weil die Reihenfolge der X Werte eine wichtige Information enthält. Eine Linie verbindet die Werte und zeigt dadurch Veränderungen sowie Entwicklungen besonders deutlich.
    if x_enthaelt_jahreszahlen:
        return {
            "typ": "linie",
            "begruendung": "Die erste Spalte enthält aufsteigende Jahreszahlen und eine weitere Spalte enthält numerische Werte. Deshalb eignet sich ein Liniendiagramm am besten, um den Verlauf über die Zeit darzustellen.",
        }

    if x_enthaelt_fortlaufende_zahlen:
        return {
            "typ": "linie",
            "begruendung": "Die erste Spalte enthält fortlaufende Zahlen und eine weitere Spalte enthält numerische Werte. Deshalb eignet sich ein Liniendiagramm am besten, um die Entwicklung in der richtigen Reihenfolge darzustellen.",
        }

    # Erst nach der Prüfung auf eine Zeitreihe wird untersucht, ob die Zeilen Anteile eines Ganzen darstellen könnten. Für einen Kreis müssen weniger als zehn Kategorien vorhanden sein, alle Y Werte müssen echt vorhanden und positiv sein und ihre Summe muss ungefähr hundert ergeben.
    anzahl_kategorien = dataframe[x_spalte].dropna().nunique()
    wenige_kategorien = 0 < anzahl_kategorien < 10
    alle_y_werte_vorhanden = len(y_werte) == len(dataframe)
    alle_y_werte_positiv = (
        not y_werte.empty
        and (y_werte > 0).all()
    )
    summe_ist_ungefaehr_hundert = (
        not y_werte.empty
        and 99 <= y_werte.sum() <= 101
    )

    # Die kleine Toleranz von einem Punkt erlaubt gerundete Prozentwerte, deren Summe knapp unter oder über hundert liegt. Sind alle Bedingungen erfüllt, ist ein Kreisdiagramm sehr wahrscheinlich passend, weil es die Anteile am Ganzen direkt sichtbar macht.
    if (
        wenige_kategorien
        and alle_y_werte_vorhanden
        and alle_y_werte_positiv
        and summe_ist_ungefaehr_hundert
    ):
        return {
            "typ": "kreis",
            "begruendung": "Die erste Spalte enthält wenige Kategorien und alle Werte sind positiv. Die Summe der Werte liegt ungefähr bei 100, deshalb stellen sie wahrscheinlich Anteile eines Ganzen dar und eignen sich gut für ein Kreisdiagramm.",
        }

    # Eine Textspalte mit numerischen Y Werten beschreibt normalerweise verschiedene benannte Kategorien. Balken erlauben einen direkten Vergleich ihrer Grössen und bleiben auch verständlich, wenn die Werte keine Anteile von hundert bilden.
    if x_spalte in text_spalten:
        return {
            "typ": "balken",
            "begruendung": "Die erste Spalte enthält Text oder Kategorien und eine weitere Spalte enthält numerische Werte. Da die Werte keine eindeutigen Anteile von 100 bilden, eignet sich ein Balkendiagramm am besten für den Vergleich.",
        }

    # Wenn keine der vorherigen Regeln eindeutig passt, wird bewusst ein Balkendiagramm verwendet. Dieser Typ ist der sicherste Fallback, weil einzelne Werte ohne angenommene zeitliche Verbindung und ohne angenommene Anteile gezeigt werden können.
    return {
        "typ": "balken",
        "begruendung": "Die Daten bilden weder eine klare Zeitreihe noch eindeutige Anteile eines Ganzen. Deshalb wird als gut verständliche Standarddarstellung ein Balkendiagramm verwendet.",
    }
