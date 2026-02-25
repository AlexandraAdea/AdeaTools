from django.db import migrations, models


def migrate_gut_to_schnell(apps, schema_editor):
    Client = apps.get_model("adeacore", "Client")
    Client.objects.filter(zahlungsverhalten="GUT").update(zahlungsverhalten="SCHNELL")


def migrate_schnell_to_gut(apps, schema_editor):
    Client = apps.get_model("adeacore", "Client")
    Client.objects.filter(zahlungsverhalten="SCHNELL").update(zahlungsverhalten="GUT")


class Migration(migrations.Migration):

    dependencies = [
        ("adeacore", "0033_client_zahlungsverhalten"),
    ]

    operations = [
        migrations.RunPython(migrate_gut_to_schnell, migrate_schnell_to_gut),
        migrations.AlterField(
            model_name="client",
            name="zahlungsverhalten",
            field=models.CharField(
                choices=[
                    ("SCHNELL", "⭐⭐⭐⭐ Schnell zahlt"),
                    ("NORMAL", "⭐⭐⭐ Normal / Neukunde"),
                    ("LANGSAM", "⭐⭐ Langsam zahlt"),
                    ("SCHLECHT", "⭐ Schlecht zahlt"),
                ],
                default="NORMAL",
                help_text="Einschätzung des Zahlungsverhaltens für Priorisierung in Aufgabenlisten.",
                max_length=20,
                verbose_name="Zahlungsverhalten",
            ),
        ),
    ]
