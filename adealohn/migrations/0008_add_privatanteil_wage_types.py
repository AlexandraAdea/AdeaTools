# Generated migration for Privatanteil WageTypes

from django.db import migrations


def create_privatanteil_wage_types(apps, schema_editor):
    """
    Erstellt WageTypes für Privatanteile (Auto/Telefon) gemäss Schweizer Recht.
    Privatanteile sind voll AHV-/Steuer-/QST-pflichtig und gelten als Lohn.
    """
    WageType = apps.get_model('adealohn', 'WageType')
    
    wage_types = [
        {
            'code': 'PRIVATANTEIL_AUTO',
            'name': 'Privatanteil Auto',
            'category': 'SACHLEISTUNG',
            'is_lohnwirksam': True,
            'qst_relevant': True,
            'ahv_relevant': True,
            'alv_relevant': True,
            'uv_relevant': True,
            'bvg_relevant': True,
            'taxable': True,
            'description': 'Privatanteil Geschäftswagen (voll AHV-/Steuer-/QST-pflichtig).',
        },
        {
            'code': 'PRIVATANTEIL_TELEFON',
            'name': 'Privatanteil Telefon',
            'category': 'SACHLEISTUNG',
            'is_lohnwirksam': True,
            'qst_relevant': True,
            'ahv_relevant': True,
            'alv_relevant': True,
            'uv_relevant': True,
            'bvg_relevant': True,
            'taxable': True,
            'description': 'Privatanteil Telefon/Internet (voll AHV-/Steuer-/QST-pflichtig).',
        },
    ]
    
    for wt_data in wage_types:
        WageType.objects.get_or_create(
            code=wt_data['code'],
            defaults=wt_data,
        )


def remove_privatanteil_wage_types(apps, schema_editor):
    WageType = apps.get_model('adealohn', 'WageType')
    WageType.objects.filter(code__in=[
        'PRIVATANTEIL_AUTO',
        'PRIVATANTEIL_TELEFON'
    ]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('adealohn', '0007_add_spesen_wage_types'),
    ]

    operations = [
        migrations.RunPython(create_privatanteil_wage_types, remove_privatanteil_wage_types),
    ]


