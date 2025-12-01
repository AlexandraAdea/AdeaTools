# Generated migration for Family Allowance WageTypes

from django.db import migrations


def create_family_allowance_wage_types(apps, schema_editor):
    """
    Erstellt WageTypes für Kinderzulage und Ausbildungszulage mit korrekten Flags:
    - is_lohnwirksam = True (gehört zum Bruttolohn)
    - qst_relevant = True (QST-pflichtig)
    - ahv_relevant = False (NICHT AHV-pflichtig)
    - alv_relevant = False (NICHT ALV-pflichtig)
    - uv_relevant = False (NICHT UVG-pflichtig)
    - bvg_relevant = False (NICHT BVG-pflichtig)
    - taxable = True (steuerbar)
    """
    WageType = apps.get_model('adealohn', 'WageType')
    
    wage_types = [
        {
            'code': 'KINDERZULAGE',
            'name': 'Kinderzulage',
            'category': 'FAMILIENZULAGE',
            'is_lohnwirksam': True,
            'qst_relevant': True,
            'ahv_relevant': False,
            'alv_relevant': False,
            'uv_relevant': False,
            'bvg_relevant': False,
            'taxable': True,
            'description': 'Kinderzulage gemäss FamZG. QST-relevant, nicht AHV/ALV/UVG/BVG-relevant.',
        },
        {
            'code': 'AUSBILDUNGSZULAGE',
            'name': 'Ausbildungszulage',
            'category': 'FAMILIENZULAGE',
            'is_lohnwirksam': True,
            'qst_relevant': True,
            'ahv_relevant': False,
            'alv_relevant': False,
            'uv_relevant': False,
            'bvg_relevant': False,
            'taxable': True,
            'description': 'Ausbildungszulage gemäss FamZG. QST-relevant, nicht AHV/ALV/UVG/BVG-relevant.',
        },
    ]
    
    for wt_data in wage_types:
        WageType.objects.get_or_create(
            code=wt_data['code'],
            defaults=wt_data,
        )
    
    # Aktualisiere bestehende FAMILIENZULAGE WageType falls vorhanden
    existing = WageType.objects.filter(code='FAMILIENZULAGE').first()
    if existing:
        existing.is_lohnwirksam = True
        existing.qst_relevant = True
        existing.ahv_relevant = False
        existing.alv_relevant = False
        existing.uv_relevant = False
        existing.bvg_relevant = False
        existing.taxable = True
        existing.description = 'Familienzulage (allgemein). QST-relevant, nicht AHV/ALV/UVG/BVG-relevant.'
        existing.save()


def remove_family_allowance_wage_types(apps, schema_editor):
    WageType = apps.get_model('adealohn', 'WageType')
    WageType.objects.filter(code__in=['KINDERZULAGE', 'AUSBILDUNGSZULAGE']).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('adealohn', '0005_add_family_allowance_parameter'),
    ]

    operations = [
        migrations.RunPython(create_family_allowance_wage_types, remove_family_allowance_wage_types),
    ]


