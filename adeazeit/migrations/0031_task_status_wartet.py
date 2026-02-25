from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("adeazeit", "0030_task_auftragsdatum"),
    ]

    operations = [
        migrations.AlterField(
            model_name="task",
            name="status",
            field=models.CharField(
                choices=[
                    ("OFFEN", "Offen"),
                    ("IN_ARBEIT", "In Arbeit"),
                    ("WARTET", "Wartet auf Kunde"),
                    ("ERLEDIGT", "Erledigt"),
                ],
                default="OFFEN",
                max_length=20,
                verbose_name="Status",
            ),
        ),
    ]
