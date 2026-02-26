from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("adeacore", "0035_update_invoice_vat_default_to_8_1"),
    ]

    operations = [
        migrations.AddField(
            model_name="companydata",
            name="mwst_pflichtig",
            field=models.BooleanField(
                default=True,
                help_text="Gilt für den Rechnungssteller (Adea Treuhand). Wenn aktiv, wird MWST auf Rechnungen berechnet.",
                verbose_name="MWST-pflichtig",
            ),
        ),
        migrations.AddField(
            model_name="companydata",
            name="mwst_satz",
            field=models.DecimalField(
                decimal_places=2,
                default=8.1,
                help_text="Standard-MWST-Satz für Rechnungen (z.B. 8.1).",
                max_digits=5,
                verbose_name="MWST-Satz (%)",
            ),
        ),
    ]
