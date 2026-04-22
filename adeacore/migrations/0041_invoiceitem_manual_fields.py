from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("adeacore", "0040_invoice_discount_amount"),
    ]

    operations = [
        migrations.AddField(
            model_name="invoiceitem",
            name="item_source",
            field=models.CharField(
                choices=[("AUTO", "Aus Zeiterfassung"), ("MANUAL", "Manuell")],
                default="AUTO",
                help_text="Wurde die Position automatisch aus der Zeiterfassung erstellt oder manuell erfasst?",
                max_length=10,
                verbose_name="Positionsquelle",
            ),
        ),
        migrations.AddField(
            model_name="invoiceitem",
            name="pricing_type",
            field=models.CharField(
                choices=[("TIME", "Stunden / Menge"), ("FIXED", "Fixbetrag")],
                default="TIME",
                help_text="Zeitbasierte Position oder fixer Betrag",
                max_length=10,
                verbose_name="Preisart",
            ),
        ),
        migrations.AddField(
            model_name="invoiceitem",
            name="title",
            field=models.CharField(
                blank=True,
                default="",
                help_text="Kurzer Titel der Rechnungsposition",
                max_length=255,
                verbose_name="Titel",
            ),
        ),
        migrations.AlterField(
            model_name="invoiceitem",
            name="employee_name",
            field=models.CharField(
                blank=True,
                default="",
                help_text="Name der Mitarbeiterin",
                max_length=255,
                verbose_name="Mitarbeiterin",
            ),
        ),
        migrations.AlterField(
            model_name="invoiceitem",
            name="service_type_code",
            field=models.CharField(
                blank=True,
                default="",
                help_text="Service-Typ Code (z.B. STEU, BUCH)",
                max_length=50,
                verbose_name="Service-Typ",
            ),
        ),
    ]
