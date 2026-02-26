from django.db import migrations, models


def seed_primary_location(apps, schema_editor):
    CompanyData = apps.get_model("adeacore", "CompanyData")
    CompanyLocation = apps.get_model("adeacore", "CompanyLocation")

    for company in CompanyData.objects.all():
        has_location = CompanyLocation.objects.filter(company=company).exists()
        if has_location:
            continue

        street = (company.street or "").strip()
        zipcode = (company.zipcode or "").strip()
        city = (company.city or "").strip()
        if not street and not (zipcode and city):
            continue

        CompanyLocation.objects.create(
            company=company,
            name="Standort 1",
            street=street or "-",
            house_number=(company.house_number or "").strip(),
            zipcode=zipcode or "-",
            city=city or "-",
            country=(company.country or "Schweiz").strip(),
            is_active=True,
            sort_order=10,
        )


class Migration(migrations.Migration):

    dependencies = [
        ("adeacore", "0037_apply_company_vat_to_existing_invoices"),
    ]

    operations = [
        migrations.CreateModel(
            name="CompanyLocation",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(blank=True, max_length=100, verbose_name="Bezeichnung")),
                ("street", models.CharField(max_length=255, verbose_name="Strasse")),
                ("house_number", models.CharField(blank=True, max_length=50, verbose_name="Hausnummer")),
                ("zipcode", models.CharField(max_length=20, verbose_name="PLZ")),
                ("city", models.CharField(max_length=255, verbose_name="Ort")),
                ("country", models.CharField(default="Schweiz", max_length=100, verbose_name="Land")),
                ("is_active", models.BooleanField(default=True, verbose_name="Aktiv")),
                ("sort_order", models.PositiveIntegerField(default=10, verbose_name="Sortierung")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "company",
                    models.ForeignKey(
                        on_delete=models.deletion.CASCADE,
                        related_name="locations",
                        to="adeacore.companydata",
                        verbose_name="Firma",
                    ),
                ),
            ],
            options={
                "verbose_name": "Standort",
                "verbose_name_plural": "Standorte",
                "ordering": ["sort_order", "id"],
            },
        ),
        migrations.RunPython(seed_primary_location, migrations.RunPython.noop),
    ]
