# Dateiname: 0001_initial.py
# Beschreibung: Diese Datei erstellt die ersten Datenbanktabellen für Datensätze, Datenpunkte und Diagramme. Django führt diese Schritte beim Einrichten oder Aktualisieren der Datenbank aus.

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Datensatz',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200)),
                ('beschreibung', models.TextField(blank=True)),
                ('erstellt_am', models.DateTimeField(auto_now_add=True)),
                ('quelldatei', models.FileField(blank=True, null=True, upload_to='uploads/')),
                ('quelle_url', models.URLField(blank=True)),
                ('dateiformat', models.CharField(blank=True, choices=[('csv', 'CSV'), ('json', 'JSON')], max_length=10)),
            ],
        ),
        migrations.CreateModel(
            name='Datenpunkt',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('x_wert', models.CharField(max_length=200)),
                ('y_wert', models.FloatField()),
                ('kategorie', models.CharField(blank=True, max_length=100)),
                ('reihenfolge', models.PositiveIntegerField(default=0)),
                ('datensatz', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='datenpunkte', to='visualisierung.datensatz')),
            ],
            options={
                'ordering': ['reihenfolge'],
            },
        ),
        migrations.CreateModel(
            name='Diagramm',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('typ', models.CharField(choices=[('linie', 'Linie'), ('balken', 'Balken'), ('kreis', 'Kreis')], max_length=10)),
                ('titel', models.CharField(max_length=200)),
                ('x_beschriftung', models.CharField(blank=True, max_length=100)),
                ('y_beschriftung', models.CharField(blank=True, max_length=100)),
                ('automatisch_gewaehlt', models.BooleanField(default=True)),
                ('erstellt_am', models.DateTimeField(auto_now_add=True)),
                ('datensatz', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='diagramme', to='visualisierung.datensatz')),
            ],
        ),
    ]
