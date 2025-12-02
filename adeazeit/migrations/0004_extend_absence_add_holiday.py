# Generated manually for extending Absence model and adding Holiday model

from django.db import migrations, models
from django.db.migrations.operations import SeparateDatabaseAndState


class Migration(migrations.Migration):

    dependencies = [
        ('adeazeit', '0003_remove_absence_index'),
    ]

    operations = [
        SeparateDatabaseAndState(
            database_operations=[
                # Database operations: Rename fields in DB
                migrations.RunSQL(
                    "ALTER TABLE adeazeit_absence RENAME COLUMN mitarbeiter_id TO employee_id;",
                    reverse_sql="ALTER TABLE adeazeit_absence RENAME COLUMN employee_id TO mitarbeiter_id;",
                ),
                migrations.RunSQL(
                    "ALTER TABLE adeazeit_absence RENAME COLUMN typ TO absence_type;",
                    reverse_sql="ALTER TABLE adeazeit_absence RENAME COLUMN absence_type TO typ;",
                ),
                migrations.RunSQL(
                    "ALTER TABLE adeazeit_absence RENAME COLUMN datum_von TO date_from;",
                    reverse_sql="ALTER TABLE adeazeit_absence RENAME COLUMN date_from TO datum_von;",
                ),
                migrations.RunSQL(
                    "ALTER TABLE adeazeit_absence RENAME COLUMN datum_bis TO date_to;",
                    reverse_sql="ALTER TABLE adeazeit_absence RENAME COLUMN date_to TO datum_bis;",
                ),
                migrations.RunSQL(
                    "ALTER TABLE adeazeit_absence RENAME COLUMN kommentar TO comment;",
                    reverse_sql="ALTER TABLE adeazeit_absence RENAME COLUMN comment TO kommentar;",
                ),
                migrations.RunSQL(
                    "ALTER TABLE adeazeit_absence DROP COLUMN updated_at;",
                    reverse_sql="ALTER TABLE adeazeit_absence ADD COLUMN updated_at datetime;",
                ),
                migrations.RunSQL(
                    "ALTER TABLE adeazeit_absence ADD COLUMN full_day bool DEFAULT 1;",
                    reverse_sql="ALTER TABLE adeazeit_absence DROP COLUMN full_day;",
                ),
                migrations.RunSQL(
                    "ALTER TABLE adeazeit_absence ADD COLUMN hours decimal(5,2) NULL;",
                    reverse_sql="ALTER TABLE adeazeit_absence DROP COLUMN hours;",
                ),
            ],
            state_operations=[
                # State operations: Update model state
                migrations.RenameField(
                    model_name='absence',
                    old_name='mitarbeiter',
                    new_name='employee',
                ),
                migrations.RenameField(
                    model_name='absence',
                    old_name='typ',
                    new_name='absence_type',
                ),
                migrations.RenameField(
                    model_name='absence',
                    old_name='datum_von',
                    new_name='date_from',
                ),
                migrations.RenameField(
                    model_name='absence',
                    old_name='datum_bis',
                    new_name='date_to',
                ),
                migrations.RenameField(
                    model_name='absence',
                    old_name='kommentar',
                    new_name='comment',
                ),
                migrations.AddField(
                    model_name='absence',
                    name='full_day',
                    field=models.BooleanField(default=True, help_text='Wenn nicht ganztägig, Stunden angeben', verbose_name='Ganztägig'),
                ),
                migrations.AddField(
                    model_name='absence',
                    name='hours',
                    field=models.DecimalField(blank=True, decimal_places=2, help_text='Nur bei Teilzeit-Abwesenheit', max_digits=5, null=True, verbose_name='Stunden'),
                ),
                migrations.RemoveField(
                    model_name='absence',
                    name='updated_at',
                ),
                migrations.AlterModelOptions(
                    name='absence',
                    options={'ordering': ['-date_from', 'employee'], 'verbose_name': 'Abwesenheit', 'verbose_name_plural': 'Abwesenheiten'},
                ),
                migrations.AddIndex(
                    model_name='absence',
                    index=models.Index(fields=['employee', 'date_from'], name='adeazeit_abs_employe_123456_idx'),
                ),
                migrations.CreateModel(
                    name='Holiday',
                    fields=[
                        ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                        ('name', models.CharField(max_length=255, verbose_name='Name')),
                        ('date', models.DateField(verbose_name='Datum')),
                        ('canton', models.CharField(blank=True, help_text="z.B. 'AG', 'ZH'. Leer = CH-weit", max_length=10, verbose_name='Kanton')),
                        ('is_official', models.BooleanField(default=True, verbose_name='Offizieller Feiertag')),
                    ],
                    options={
                        'verbose_name': 'Feiertag',
                        'verbose_name_plural': 'Feiertage',
                        'ordering': ['date'],
                        'unique_together': {('date', 'canton')},
                    },
                ),
            ],
        ),
    ]

