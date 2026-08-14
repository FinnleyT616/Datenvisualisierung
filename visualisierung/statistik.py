# Dateiname: statistik.py
# Beschreibung: Diese Datei berechnet einfache statistische Kennzahlen aus gespeicherten Datenpunkten. Die Ergebnisse können später gemeinsam mit einem Diagramm auf der Webseite angezeigt werden.

from statistics import mean, median


def kennzahlen_berechnen(datenpunkte_queryset) -> dict:
    """Berechnet die Anzahl, den Mittelwert, den Median, das Minimum und das Maximum der Y Werte aus einer Datenpunkt Abfrage. Das Ergebnis wird als einfaches Dictionary zurückgegeben. Bei einer leeren Abfrage ist die Anzahl null und die übrigen Werte bleiben leer."""

    # Es werden nur die Y Werte aus der Datenbank geladen, weil die anderen Felder für diese einfachen Berechnungen nicht benötigt werden. Die Liste kann danach direkt mit den verständlichen Funktionen aus dem statistics Modul ausgewertet werden.
    y_werte = list(
        datenpunkte_queryset.values_list(
            "y_wert",
            flat=True,
        )
    )

    # Eine leere Liste besitzt keinen Mittelwert, Median, kleinsten oder grössten Wert. None zeigt diesen Zustand klar an und kann später in einer Vorlage durch einen passenden deutschen Hinweis ersetzt werden.
    if not y_werte:
        return {
            "anzahl": 0,
            "mittelwert": None,
            "median": None,
            "minimum": None,
            "maximum": None,
        }

    # Die fünf Kennzahlen werden bewusst einfach und direkt berechnet. Dadurch bleibt die Funktion leicht verständlich und jeder Wert kann über seinen deutschen Schlüssel aus dem Dictionary gelesen werden.
    return {
        "anzahl": len(y_werte),
        "mittelwert": mean(y_werte),
        "median": median(y_werte),
        "minimum": min(y_werte),
        "maximum": max(y_werte),
    }
