from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("adeacore", "0032_rename_payroll_fields_to_german"),
    ]

    operations = [
        migrations.AddField(
            model_name="client",
            name="zahlungsverhalten",
            field=models.CharField(
                choices=[
                    ("GUT", "Gut"),
                    ("NORMAL", "Normal"),
                    ("LANGSAM", "Langsam"),
                    ("SCHLECHT", "Schlecht"),
                ],
                default="NORMAL",
                help_text="Einschätzung des Zahlungsverhaltens für Priorisierung in Aufgabenlisten.",
                max_length=20,
                verbose_name="Zahlungsverhalten",
            ),
        ),
    ]
