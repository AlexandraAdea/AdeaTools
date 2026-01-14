from django.db import migrations

INDEX_NAME = "adeazeit_ab_mitarbe_ada11c_idx"

def drop_index_if_exists(apps, schema_editor):
    with schema_editor.connection.cursor() as cursor:
        vendor = schema_editor.connection.vendor

        if vendor in ("postgresql", "sqlite"):
            cursor.execute(f'DROP INDEX IF EXISTS "{INDEX_NAME}";')
        else:
            # Fallback: versuchen und Fehler ignorieren
            try:
                cursor.execute(f'DROP INDEX {INDEX_NAME};')
            except Exception:
                pass

class Migration(migrations.Migration):
    dependencies = [
        ("adeazeit", "0012_task_remove_absence_adeazeit_ab_mitarbe_ada11c_idx_and_more"),
    ]

    operations = [
        migrations.RunPython(drop_index_if_exists, migrations.RunPython.noop),
    ]
