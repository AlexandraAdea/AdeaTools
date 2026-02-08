# Generated migration: Familienzulagen sind Durchlaufender Posten SVA, nicht lohnwirksam

from django.db import migrations


def set_family_allowance_not_lohnwirksam(apps, schema_editor):
    """
    Setzt is_lohnwirksam=False für Familienzulagen.
    Familienzulagen sind Durchlaufender Posten SVA und gehören nicht zum Bruttolohn.
    Sie werden separat als "Spesen und Zulagen" addiert.
    """
    WageType = apps.get_model('adealohn', 'WageType')
    
    # Aktualisiere alle Familienzulagen-WageTypes
    WageType.objects.filter(
        code__in=['KINDERZULAGE', 'AUSBILDUNGSZULAGE', 'FAMILIENZULAGE']
    ).update(is_lohnwirksam=False)


def reverse_set_family_allowance_not_lohnwirksam(apps, schema_editor):
    """
    Setzt is_lohnwirksam=True zurück (für Rollback).
    """
    WageType = apps.get_model('adealohn', 'WageType')
    
    WageType.objects.filter(
        code__in=['KINDERZULAGE', 'AUSBILDUNGSZULAGE', 'FAMILIENZULAGE']
    ).update(is_lohnwirksam=True)


class Migration(migrations.Migration):

    dependencies = [
        ('adealohn', '0014_add_bvg_wage_types'),
    ]

    operations = [
        migrations.RunPython(set_family_allowance_not_lohnwirksam, reverse_set_family_allowance_not_lohnwirksam),
    ]
