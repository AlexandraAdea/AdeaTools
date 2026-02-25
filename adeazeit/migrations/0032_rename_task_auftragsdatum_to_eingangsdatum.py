from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("adeazeit", "0031_task_status_wartet"),
    ]

    operations = [
        migrations.RenameField(
            model_name="task",
            old_name="auftragsdatum",
            new_name="eingangsdatum",
        ),
        migrations.AlterField(
            model_name="task",
            name="eingangsdatum",
            field=models.DateField(
                blank=True,
                null=True,
                verbose_name="Unterlagen eingegangen",
                help_text="Wann hat der Kunde seine Unterlagen vollständig eingereicht?",
            ),
        ),
    ]
