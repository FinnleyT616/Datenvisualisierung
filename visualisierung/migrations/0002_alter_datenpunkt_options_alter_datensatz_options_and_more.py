# Dateiname: 0002_alter_datenpunkt_options_alter_datensatz_options_and_more.py
# Beschreibung: Diese Datei ergänzt die richtigen deutschen Namen für die drei Modelle im Verwaltungsbereich. Dadurch zeigt Django auch bei mehreren Einträgen verständliche Bezeichnungen an.

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('visualisierung', '0001_initial'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='datenpunkt',
            options={'ordering': ['reihenfolge'], 'verbose_name': 'Datenpunkt', 'verbose_name_plural': 'Datenpunkte'},
        ),
        migrations.AlterModelOptions(
            name='datensatz',
            options={'verbose_name': 'Datensatz', 'verbose_name_plural': 'Datensätze'},
        ),
        migrations.AlterModelOptions(
            name='diagramm',
            options={'verbose_name': 'Diagramm', 'verbose_name_plural': 'Diagramme'},
        ),
    ]
