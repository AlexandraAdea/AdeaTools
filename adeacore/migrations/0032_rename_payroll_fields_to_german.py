# Generated migration for field renames to German
from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ('adeacore', '0031_add_pensum_iban_to_employee'),
    ]

    operations = [
        migrations.RenameField(
            model_name='payrollrecord',
            old_name='gross_salary',
            new_name='bruttolohn',
        ),
        migrations.RenameField(
            model_name='payrollrecord',
            old_name='net_salary',
            new_name='nettolohn',
        ),
        migrations.RenameField(
            model_name='payrollrecord',
            old_name='qst_amount',
            new_name='qst_abzug',
        ),
    ]
