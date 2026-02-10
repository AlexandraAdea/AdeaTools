# Generated migration for Spesen WageTypes

from django.db import migrations, models


def create_spesen_wage_types(apps, schema_editor):
    """
    Erstellt WageTypes für Spesen gemäss Schweizer Gesetz (Stand 2025):
    - SPESEN_EFFEKTIV: Effektiver Kostenersatz gegen Beleg (immer AHV- und steuerfrei)
    - SPESEN_PAUSCHALE_AHV_FREI: Pauschalspesen AHV-frei (nur bei genehmigtem Reglement)
    - SPESEN_PAUSCHALE_AHV_PFLICHTIG: Pauschalspesen als Lohn (AHV-pflichtig)
    
    Hinweis: KTG wird über uv_relevant gesteuert (KTG-Basis = UV-Basis).
    """
    WageType = apps.get_model('adealohn', 'WageType')
    
    wage_types = [
        {
            'code': 'SPESEN_EFFEKTIV',
            'name': 'Spesen effektiv',
            'category': 'SPESEN',
            'is_lohnwirksam': False,
            'qst_relevant': False,
            'ahv_relevant': False,
            'alv_relevant': False,
            'uv_relevant': False,
            'bvg_relevant': False,
            'taxable': False,
            'description': 'Effektiver Spesenersatz gegen Beleg. Immer AHV- und steuerfrei.',
        },
        {
            'code': 'SPESEN_PAUSCHALE_AHV_FREI',
            'name': 'Spesen pauschal (AHV-frei)',
            'category': 'SPESEN',
            'is_lohnwirksam': False,
            'qst_relevant': False,
            'ahv_relevant': False,
            'alv_relevant': False,
            'uv_relevant': False,
            'bvg_relevant': False,
            'taxable': False,
            'description': 'Nur AHV-/steuerfrei bei genehmigtem Spesenreglement oder gemäss behördlicher Praxis.',
        },
        {
            'code': 'SPESEN_PAUSCHALE_AHV_PFLICHTIG',
            'name': 'Spesen pauschal (AHV-pflichtig)',
            'category': 'SPESEN',
            'is_lohnwirksam': True,
            'qst_relevant': True,
            'ahv_relevant': True,
            'alv_relevant': True,
            'uv_relevant': True,
            'bvg_relevant': True,
            'taxable': True,
            'description': 'Pauschalspesen ohne genehmigtes Reglement: gelten als Lohn und sind AHV- / ALV- / UVG- / BVG- / QST-pflichtig. KTG wird über UV-Basis berechnet.',
        },
    ]
    
    for wt_data in wage_types:
        WageType.objects.get_or_create(
            code=wt_data['code'],
            defaults=wt_data,
        )


def remove_spesen_wage_types(apps, schema_editor):
    WageType = apps.get_model('adealohn', 'WageType')
    WageType.objects.filter(code__in=[
        'SPESEN_EFFEKTIV',
        'SPESEN_PAUSCHALE_AHV_FREI',
        'SPESEN_PAUSCHALE_AHV_PFLICHTIG'
    ]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('adealohn', '0006_add_family_allowance_wage_types'),
    ]

    operations = [
        # Feld zuerst vergrössern, damit lange Codes (bis 30 Zeichen) reinpassen
        migrations.AlterField(
            model_name='wagetype',
            name='code',
            field=models.CharField(max_length=50, unique=True),
        ),
        migrations.RunPython(create_spesen_wage_types, remove_spesen_wage_types),
    ]

