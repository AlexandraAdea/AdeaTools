# Generated manually to remove old index before renaming fields

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('adeazeit', '0002_extend_employee_internal'),
    ]

    operations = [
        migrations.RunSQL(
            "DROP INDEX IF EXISTS adeazeit_ab_mitarbe_ada11c_idx;",
            reverse_sql=migrations.RunSQL.noop,
        ),
    ]
