from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("adeazeit", "0028_merge_20260114_1702"),
    ]

    operations = [
        migrations.AddField(
            model_name="task",
            name="tagesplan",
            field=models.BooleanField(
                default=False,
                help_text="Markiert die Aufgabe für den Tagesplan (Widget 'Heute zu erledigen').",
                verbose_name="Heute einplanen",
            ),
        ),
    ]
