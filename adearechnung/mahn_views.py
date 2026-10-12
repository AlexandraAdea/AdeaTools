"""Views für das Mahnwesen (Mahnlauf, Mahnsperre, Mahnung-PDF)."""
from datetime import date

from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.views import View
from django.views.generic import TemplateView

from adeacore.models import Invoice
from adeazeit.mixins import ManagerOrAdminRequiredMixin

from . import mahn_service
from .mahn_pdf import MahnungPDFGenerator
from .models import Mahnung


def _parse_stichtag(raw) -> date | None:
    try:
        return date.fromisoformat((raw or "").strip())
    except ValueError:
        return None


def _zurueck(stichtag: date | None = None):
    url = reverse("adearechnung:mahnlauf")
    return redirect(f"{url}?stichtag={stichtag.isoformat()}" if stichtag else url)


class MahnlaufView(ManagerOrAdminRequiredMixin, TemplateView):
    """Vorschau der fälligen Mahnungen zum Stichtag und Auslösen des Mahnlaufs."""

    template_name = "adearechnung/mahnlauf.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        raw = self.request.GET.get("stichtag")
        stichtag = _parse_stichtag(raw) or date.today()
        if raw and _parse_stichtag(raw) is None:
            messages.error(self.request, "Ungültiger Stichtag, es wird das heutige Datum verwendet.")

        ergebnisse = mahn_service.vorschau(stichtag)
        ctx.update(
            stichtag=stichtag,
            heute=date.today(),
            mahnen=[e for e in ergebnisse if e.aktion == "mahnen"],
            betreibung=[e for e in ergebnisse if e.aktion == "betreibung_pruefen"],
            mahnungen=Mahnung.objects.select_related("invoice__client")[:100],
            gesperrt=Invoice.objects.filter(mahnsperre=True).select_related("client"),
        )
        return ctx

    def post(self, request, *args, **kwargs):
        stichtag = _parse_stichtag(request.POST.get("stichtag"))
        if stichtag is None:
            messages.error(request, "Ungültiger Stichtag.")
            return _zurueck()
        if stichtag > date.today():
            messages.error(request, "Der Stichtag darf nicht in der Zukunft liegen.")
            return _zurueck(stichtag)

        try:
            ids = [int(x) for x in request.POST.getlist("rechnung")]
        except ValueError:
            ids = []
        if not ids:
            messages.error(request, "Keine Rechnung ausgewählt.")
            return _zurueck(stichtag)

        erzeugt, _ = mahn_service.mahnlauf_ausfuehren(stichtag, request.user, nur_rechnungen=ids)
        if erzeugt:
            messages.success(request, f"{len(erzeugt)} Mahnung(en) erzeugt.")
        else:
            messages.info(request, "Keine neue Mahnung erzeugt (bereits vorhanden oder nicht mehr fällig).")
        return _zurueck(stichtag)


class MahnungPDFView(ManagerOrAdminRequiredMixin, View):
    def get(self, request, pk):
        mahnung = get_object_or_404(Mahnung.objects.select_related("invoice__client"), pk=pk)
        return MahnungPDFGenerator().generate_mahnung_pdf(mahnung)


class MahnungVersendetView(ManagerOrAdminRequiredMixin, View):
    """Markiert eine Mahnung als versendet (heutiges Datum)."""

    def post(self, request, pk):
        mahnung = get_object_or_404(Mahnung, pk=pk)
        if mahnung.versendet_am is None:
            mahnung.versendet_am = date.today()
            mahnung.save(update_fields=["versendet_am"])
            messages.success(request, "Mahnung als versendet markiert.")
        return _zurueck()


class InvoiceMahnsperreView(ManagerOrAdminRequiredMixin, View):
    """Setzt oder hebt die Mahnsperre einer Rechnung auf."""

    def post(self, request, pk):
        invoice = get_object_or_404(Invoice, pk=pk)
        if invoice.mahnsperre:
            invoice.mahnsperre = False
            invoice.mahnsperre_grund = ""
            messages.success(request, f"Mahnsperre für {invoice.invoice_number} aufgehoben.")
        else:
            invoice.mahnsperre = True
            invoice.mahnsperre_grund = (request.POST.get("grund") or "").strip()[:200]
            messages.success(request, f"Mahnsperre für {invoice.invoice_number} gesetzt.")
        # save() berechnet den Zahlungsstatus neu, Beträge bleiben unverändert
        invoice.save()
        return _zurueck(_parse_stichtag(request.POST.get("stichtag")))
