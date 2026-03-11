from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("adeacore", "0039_increase_companydata_iban_length"),
    ]

    operations = [
        migrations.AddField(
            model_name="invoice",
            name="discount_amount",
            field=models.DecimalField(
                decimal_places=2,
                default=0,
                help_text="Rabatt in CHF (vor MWST).",
                max_digits=10,
                verbose_name="Rabattbetrag",
            ),
        ),
    ]
