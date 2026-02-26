from decimal import Decimal, ROUND_HALF_UP

from django.db import migrations


def apply_company_vat(apps, schema_editor):
    CompanyData = apps.get_model("adeacore", "CompanyData")
    Invoice = apps.get_model("adeacore", "Invoice")
    InvoiceItem = apps.get_model("adeacore", "InvoiceItem")

    company = CompanyData.objects.filter(pk=1).first()
    if company and company.mwst_pflichtig:
        vat_rate = Decimal(str(company.mwst_satz or Decimal("8.1")))
    else:
        vat_rate = Decimal("0.00")

    quant = Decimal("0.01")

    for invoice in Invoice.objects.all():
        net_amount = Decimal(str(invoice.net_amount or 0))
        vat_amount = (net_amount * vat_rate / Decimal("100")).quantize(quant, rounding=ROUND_HALF_UP)
        gross_amount = (net_amount + vat_amount).quantize(quant, rounding=ROUND_HALF_UP)

        invoice.vat_rate = vat_rate
        invoice.vat_amount = vat_amount
        invoice.amount = gross_amount
        invoice.save(update_fields=["vat_rate", "vat_amount", "amount"])

    for item in InvoiceItem.objects.all():
        net_amount = Decimal(str(item.net_amount or 0))
        vat_amount = (net_amount * vat_rate / Decimal("100")).quantize(quant, rounding=ROUND_HALF_UP)
        gross_amount = (net_amount + vat_amount).quantize(quant, rounding=ROUND_HALF_UP)

        item.vat_rate = vat_rate
        item.vat_amount = vat_amount
        item.gross_amount = gross_amount
        item.save(update_fields=["vat_rate", "vat_amount", "gross_amount"])


class Migration(migrations.Migration):

    dependencies = [
        ("adeacore", "0036_add_companydata_vat_settings"),
    ]

    operations = [
        migrations.RunPython(apply_company_vat, migrations.RunPython.noop),
    ]
