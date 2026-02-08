# Generated migration for BVG WageTypes

from django.db import migrations


def create_bvg_wage_types(apps, schema_editor):
    """
    Erstellt WageTypes für manuelle BVG-Beiträge (Arbeitnehmer und Arbeitgeber).
    
    WICHTIG: Diese WageTypes sind NICHT lohnwirksam (sind Abzüge, nicht Lohn)
    und fließen NICHT in die BVG-Basis ein (bvg_relevant=False), da sie bereits
    Beiträge sind, nicht Lohnbestandteile.
    """
    WageType = apps.get_model('adealohn', 'WageType')
    
    wage_types = [
        {
            'code': 'BVG_AN',
            'name': 'BVG Arbeitnehmer',
            'category': 'KORREKTUR',
            'is_lohnwirksam': False,  # WICHTIG: Abzug, nicht Lohn
            'qst_relevant': False,
            'ahv_relevant': False,
            'alv_relevant': False,
            'uv_relevant': False,
            'bvg_relevant': False,  # WICHTIG: Fließt nicht in BVG-Basis ein
            'taxable': False,
            'description': 'Manueller BVG-Arbeitnehmerbeitrag (Abzug). Wird direkt als Abzug behandelt, nicht als Lohnbestandteil.',
        },
        {
            'code': 'BVG_AG',
            'name': 'BVG Arbeitgeber',
            'category': 'KORREKTUR',
            'is_lohnwirksam': False,  # WICHTIG: Abzug, nicht Lohn
            'qst_relevant': False,
            'ahv_relevant': False,
            'alv_relevant': False,
            'uv_relevant': False,
            'bvg_relevant': False,  # WICHTIG: Fließt nicht in BVG-Basis ein
            'taxable': False,
            'description': 'Manueller BVG-Arbeitgeberbeitrag (für Dokumentation). Wird direkt als Arbeitgeberbeitrag behandelt.',
        },
    ]
    
    for wt_data in wage_types:
        WageType.objects.get_or_create(
            code=wt_data['code'],
            defaults=wt_data,
        )


def remove_bvg_wage_types(apps, schema_editor):
    WageType = apps.get_model('adealohn', 'WageType')
    WageType.objects.filter(code__in=[
        'BVG_AN',
        'BVG_AG'
    ]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('adealohn', '0013_ahvparameter_alvparameter_vkparameter_and_more'),
    ]

    operations = [
        migrations.RunPython(create_bvg_wage_types, remove_bvg_wage_types),
    ]
