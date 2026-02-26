from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("adeacore", "0034_update_client_zahlungsverhalten_choices"),
    ]

    operations = [
        migrations.AlterField(
            model_name="invoice",
            name="vat_rate",
            field=models.DecimalField(
                decimal_places=2,
                default=8.1,
                help_text="MWST-Satz (z.B. 8.1)",
                max_digits=5,
                verbose_name="MWST-Satz (%)",
            ),
        ),
        migrations.AlterField(
            model_name="invoiceitem",
            name="vat_rate",
            field=models.DecimalField(
                decimal_places=2,
                default=0,
                help_text="MWST-Satz (z.B. 8.1)",
                max_digits=5,
                verbose_name="MWST-Satz (%)",
            ),
        ),
    ]
