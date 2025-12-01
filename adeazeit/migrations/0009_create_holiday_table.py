# Generated manually to create Holiday table

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('adeazeit', '0008_remove_absence_adeazeit_ab_mitarbe_ada11c_idx_and_more'),
    ]

    operations = [
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
            },
        ),
        migrations.AlterUniqueTogether(
            name='holiday',
            unique_together={('date', 'canton')},
        ),
    ]
