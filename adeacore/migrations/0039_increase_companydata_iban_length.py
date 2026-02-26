from django.db import migrations

import adeacore.fields


class Migration(migrations.Migration):

    dependencies = [
        ("adeacore", "0038_companylocation"),
    ]

    operations = [
        migrations.AlterField(
            model_name="companydata",
            name="iban",
            field=adeacore.fields.EncryptedCharField(
                blank=True, help_text="IBAN für QR-Rechnung", max_length=500, verbose_name="IBAN"
            ),
        ),
    ]
