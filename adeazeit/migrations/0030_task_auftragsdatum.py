from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("adeazeit", "0029_task_tagesplan"),
    ]

    operations = [
        migrations.AddField(
            model_name="task",
            name="auftragsdatum",
            field=models.DateField(blank=True, null=True, verbose_name="Auftragsdatum"),
        ),
    ]
