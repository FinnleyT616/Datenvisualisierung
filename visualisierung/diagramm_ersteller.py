# Dateiname: diagramm_ersteller.py
# Beschreibung: Diese Datei erstellt interaktive und statische Diagramme aus einem gespeicherten Datensatz. Sie unterstützt bewusst nur Linien, Balken und Kreisdiagramme.

from pathlib import Path

import matplotlib

# Matplotlib verwendet hier eine Ausgabe ohne sichtbares Programmfenster, weil die Diagramme auf dem Server direkt als Dateien gespeichert werden. Diese Einstellung muss vor dem Import von pyplot gesetzt werden, damit sie zuverlässig angewendet wird.
matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import plotly.graph_objects as go
from django.conf import settings
from plotly.offline import plot

from .utils import datensatz_zu_dataframe


class DiagrammErsteller:
    """Diese Klasse erstellt aus einem Datensatz genau die drei erlaubten Diagrammtypen Linie, Balken und Kreis. Für die Anzeige im Browser wird Plotly verwendet und für gespeicherte Bilder oder Dokumente wird Matplotlib verwendet."""

    def __init__(self, datensatz, diagramm):
        """Speichert den Datensatz mit seinen Datenpunkten und das Diagramm Objekt mit den gewünschten Einstellungen. Dadurch können alle weiteren Methoden auf dieselben Daten, Titel und Beschriftungen zugreifen."""

        # Beide Objekte werden direkt in der Klasse gespeichert, damit beim Erstellen nicht immer wieder dieselben Angaben übergeben werden müssen. Das Diagramm Objekt enthält unter anderem den Typ, den Titel und die Beschriftungen der Achsen.
        self.datensatz = datensatz
        self.diagramm = diagramm

    def erstellen_interaktiv(self) -> str:
        """Erstellt das ausgewählte Diagramm als interaktive Plotly Figur und gibt den fertigen HTML Code als div Element zurück. Die Plotly Bibliothek wird dabei nicht in jedes Diagramm eingebettet, weil sie später einmal gemeinsam in der Vorlage geladen werden kann."""

        # Die gespeicherten Datenpunkte werden zuerst in eine Pandas Tabelle umgewandelt. Dadurch können alle drei Diagrammarten dieselbe übersichtliche Tabellenstruktur verwenden.
        dataframe = datensatz_zu_dataframe(self.datensatz)

        # Der gespeicherte Typ entscheidet, welche der genau drei erlaubten Methoden aufgerufen wird. Ein unbekannter Wert wird klar abgelehnt, damit nicht still ein falsches Diagramm angezeigt wird.
        if self.diagramm.typ == "linie":
            figur = self._liniendiagramm(dataframe, interaktiv=True)
        elif self.diagramm.typ == "balken":
            figur = self._balkendiagramm(dataframe, interaktiv=True)
        elif self.diagramm.typ == "kreis":
            figur = self._kreisdiagramm(dataframe, interaktiv=True)
        else:
            raise ValueError(
                "Dieser Diagrammtyp wird nicht unterstützt. Erlaubt sind nur Linie, Balken und Kreis."
            )

        # output_type div liefert nur das Element für die Webseite und keine vollständige HTML Seite. include_plotlyjs False verhindert, dass die grosse Plotly Bibliothek bei jedem Diagramm erneut im Quelltext enthalten ist.
        return plot(
            figur,
            output_type="div",
            include_plotlyjs=False,
        )

    def erstellen_statisch(self, format="png") -> str:
        """Erstellt das ausgewählte Diagramm als statische Matplotlib Figur und speichert es im Medienordner für Diagramme. Unterstützt werden ausschliesslich PNG und PDF. Nach dem Speichern wird der vollständige Dateipfad als Text zurückgegeben."""

        # Das Format wird in kleine Buchstaben umgewandelt, damit Eingaben wie PNG und PDF ebenfalls funktionieren. Andere Formate werden abgelehnt, weil für dieses Projekt bewusst nur Bild und Dokumentexport vorgesehen sind.
        dateiformat = format.lower()
        if dateiformat not in {"png", "pdf"}:
            raise ValueError(
                "Dieses Exportformat wird nicht unterstützt. Erlaubt sind nur PNG und PDF."
            )

        # Die Datenbankwerte werden auch für den statischen Export als Tabelle geladen. Danach wird dieselbe Auswahl nach Diagrammtyp verwendet wie bei der interaktiven Darstellung.
        dataframe = datensatz_zu_dataframe(self.datensatz)
        if self.diagramm.typ == "linie":
            figur = self._liniendiagramm(dataframe, interaktiv=False)
        elif self.diagramm.typ == "balken":
            figur = self._balkendiagramm(dataframe, interaktiv=False)
        elif self.diagramm.typ == "kreis":
            figur = self._kreisdiagramm(dataframe, interaktiv=False)
        else:
            raise ValueError(
                "Dieser Diagrammtyp wird nicht unterstützt. Erlaubt sind nur Linie, Balken und Kreis."
            )

        # Der Zielordner wird bei Bedarf erstellt, damit der Export auch in einem frisch eingerichteten Projekt funktioniert. parents True erstellt gleichzeitig fehlende übergeordnete Ordner.
        diagrammordner = Path(settings.MEDIA_ROOT) / "diagramme"
        diagrammordner.mkdir(parents=True, exist_ok=True)

        # Die Datenbanknummer des Diagramms sorgt für einen eindeutigen und leicht zuzuordnenden Dateinamen. Bei einem noch nicht gespeicherten Diagramm wird ersatzweise die Nummer des Datensatzes verwendet.
        dateinummer = self.diagramm.pk or self.datensatz.pk or "vorschau"
        dateiname = f"diagramm_{dateinummer}_{self.diagramm.typ}.{dateiformat}"
        dateipfad = diagrammordner / dateiname

        # bbox_inches tight entfernt unnötig grosse Ränder und dpi 150 sorgt bei PNG Dateien für eine gut lesbare Auflösung. Nach dem Speichern wird die Figur geschlossen, damit bei mehreren Exporten kein unnötiger Speicher belegt bleibt.
        figur.savefig(
            dateipfad,
            format=dateiformat,
            bbox_inches="tight",
            dpi=150,
        )
        plt.close(figur)
        return str(dateipfad)

    def _liniendiagramm(self, df, interaktiv=True):
        """Erstellt ein Liniendiagramm aus den X und Y Werten der übergebenen Tabelle. Wenn verschiedene Kategorien vorhanden sind, erhält jede Kategorie eine eigene Linie. Je nach Einstellung wird eine Plotly Figur oder eine Matplotlib Figur zurückgegeben."""

        # Eine Kategorie gilt nur dann als vorhanden, wenn mindestens ein Eintrag nicht leer ist. So entsteht bei Datensätzen ohne Gruppen keine unnötige Legende mit einem leeren Namen.
        hat_kategorien = (
            "kategorie" in df.columns
            and df["kategorie"].fillna("").astype(str).str.strip().ne("").any()
        )

        if interaktiv:
            figur = go.Figure()

            # Bei mehreren Gruppen wird für jede Kategorie eine eigene Spur erstellt. Plotly kann diese Linien in der Legende einzeln ein und ausblenden und zeigt beim Berühren eines Punktes den genauen Wert an.
            if hat_kategorien:
                for kategorie, gruppe in df.groupby("kategorie", sort=False):
                    figur.add_trace(
                        go.Scatter(
                            x=gruppe["x_wert"],
                            y=gruppe["y_wert"],
                            mode="lines+markers",
                            name=str(kategorie),
                        )
                    )
            else:
                figur.add_trace(
                    go.Scatter(
                        x=df["x_wert"],
                        y=df["y_wert"],
                        mode="lines+markers",
                        name=self.diagramm.titel,
                    )
                )

            figur.update_layout(
                title=self.diagramm.titel,
                xaxis_title=self.diagramm.x_beschriftung,
                yaxis_title=self.diagramm.y_beschriftung,
            )
            return figur

        # Für die statische Ausgabe wird eine Matplotlib Figur mit einer gut lesbaren Standardgrösse erstellt. Die Verarbeitung der Kategorien entspricht bewusst genau der interaktiven Version.
        figur, achse = plt.subplots(figsize=(10, 6))
        if hat_kategorien:
            for kategorie, gruppe in df.groupby("kategorie", sort=False):
                achse.plot(
                    gruppe["x_wert"],
                    gruppe["y_wert"],
                    marker="o",
                    label=str(kategorie),
                )
            achse.legend()
        else:
            achse.plot(df["x_wert"], df["y_wert"], marker="o")

        achse.set_title(self.diagramm.titel)
        achse.set_xlabel(self.diagramm.x_beschriftung)
        achse.set_ylabel(self.diagramm.y_beschriftung)
        achse.grid(True, alpha=0.3)
        figur.tight_layout()
        return figur

    def _balkendiagramm(self, df, interaktiv=True):
        """Erstellt ein Balkendiagramm aus den X und Y Werten der übergebenen Tabelle. Bei vorhandenen Kategorien werden die Balken gruppiert nebeneinander dargestellt. Die Methode unterstützt eine interaktive Plotly Figur und eine statische Matplotlib Figur."""

        # Genau wie bei der Linie wird geprüft, ob echte Kategorien vorhanden sind. Diese gemeinsame Regel sorgt dafür, dass leere Kategorien bei beiden Diagrammarten gleich behandelt werden.
        hat_kategorien = (
            "kategorie" in df.columns
            and df["kategorie"].fillna("").astype(str).str.strip().ne("").any()
        )

        if interaktiv:
            figur = go.Figure()
            if hat_kategorien:
                # Jede Kategorie wird als eigene Balkenspur hinzugefügt und Plotly ordnet gleiche X Werte durch barmode group nebeneinander an. So lassen sich die Gruppen direkt vergleichen.
                for kategorie, gruppe in df.groupby("kategorie", sort=False):
                    figur.add_trace(
                        go.Bar(
                            x=gruppe["x_wert"],
                            y=gruppe["y_wert"],
                            name=str(kategorie),
                        )
                    )
            else:
                figur.add_trace(
                    go.Bar(
                        x=df["x_wert"],
                        y=df["y_wert"],
                        name=self.diagramm.titel,
                    )
                )

            figur.update_layout(
                title=self.diagramm.titel,
                xaxis_title=self.diagramm.x_beschriftung,
                yaxis_title=self.diagramm.y_beschriftung,
                barmode="group",
            )
            return figur

        figur, achse = plt.subplots(figsize=(10, 6))
        if hat_kategorien:
            # Für gruppierte statische Balken werden zuerst alle unterschiedlichen X Beschriftungen gesammelt. Jede Kategorie erhält einen leicht verschobenen Platz innerhalb derselben Gruppe.
            x_beschriftungen = list(dict.fromkeys(df["x_wert"].astype(str)))
            kategorien = list(dict.fromkeys(df["kategorie"].astype(str)))
            positionen = np.arange(len(x_beschriftungen))
            balkenbreite = 0.8 / len(kategorien)

            for nummer, kategorie in enumerate(kategorien):
                gruppe = df[df["kategorie"].astype(str) == kategorie]
                werte_nach_x = dict(
                    zip(gruppe["x_wert"].astype(str), gruppe["y_wert"])
                )
                y_werte = [werte_nach_x.get(x_wert, 0) for x_wert in x_beschriftungen]
                verschiebung = (nummer - (len(kategorien) - 1) / 2) * balkenbreite
                achse.bar(
                    positionen + verschiebung,
                    y_werte,
                    width=balkenbreite,
                    label=kategorie,
                )

            achse.set_xticks(positionen)
            achse.set_xticklabels(x_beschriftungen)
            achse.legend()
        else:
            achse.bar(df["x_wert"].astype(str), df["y_wert"])

        achse.set_title(self.diagramm.titel)
        achse.set_xlabel(self.diagramm.x_beschriftung)
        achse.set_ylabel(self.diagramm.y_beschriftung)
        figur.tight_layout()
        return figur

    def _kreisdiagramm(self, df, interaktiv=True):
        """Erstellt ein Kreisdiagramm, bei welchem Kategorien oder X Werte die einzelnen Segmente bezeichnen. Gleich benannte Segmente werden vor der Darstellung zusammengezählt. Die Methode gibt je nach Einstellung eine Plotly Figur oder eine Matplotlib Figur zurück."""

        # Wenn echte Kategorien vorhanden sind, werden sie als Segmentnamen verwendet. Ohne Kategorien dienen die X Werte als verständliche Beschriftungen für die einzelnen Teile des Kreises.
        hat_kategorien = (
            "kategorie" in df.columns
            and df["kategorie"].fillna("").astype(str).str.strip().ne("").any()
        )
        if hat_kategorien:
            segmentnamen = df["kategorie"].fillna("").astype(str)
        else:
            segmentnamen = df["x_wert"].fillna("").astype(str)

        # Eine kleine neue Tabelle fasst gleiche Namen zusammen und addiert ihre Werte. Dadurch erscheint jede Kategorie nur einmal im Kreis und die gesamte Fläche bleibt korrekt aufgeteilt.
        kreisdaten = df.assign(segmentname=segmentnamen).groupby(
            "segmentname",
            as_index=False,
            sort=False,
        )["y_wert"].sum()

        if interaktiv:
            figur = go.Figure(
                data=[
                    go.Pie(
                        labels=kreisdaten["segmentname"],
                        values=kreisdaten["y_wert"],
                    )
                ]
            )
            figur.update_layout(title=self.diagramm.titel)
            return figur

        # Matplotlib zeigt zusätzlich zu den Segmentnamen auch die berechneten Prozentwerte an. startangle 90 beginnt oben und sorgt für eine vertraute Darstellung des Kreises.
        figur, achse = plt.subplots(figsize=(8, 8))
        achse.pie(
            kreisdaten["y_wert"],
            labels=kreisdaten["segmentname"],
            autopct="%1.1f%%",
            startangle=90,
        )
        achse.set_title(self.diagramm.titel)
        achse.axis("equal")
        figur.tight_layout()
        return figur
