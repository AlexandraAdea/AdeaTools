"""Verbindet Invoice/CompanyData mit der Mahnlogik und speichert Mahnungen."""
from __future__ import annotations

from datetime import date
from decimal import Decimal

from django.db import IntegrityError, transaction

from adeacore.models import CompanyData, Invoice

from . import mahnlogik
from .models import Mahnung


def config_aus_firmendaten() -> mahnlogik.Config:
    """Firmenname, IBAN, MWST-Satz und MWST-Nr. kommen aus CompanyData."""
    cd = CompanyData.get_instance()
    satz = (Decimal(cd.mwst_satz) / Decimal("100")) if cd.mwst_pflichtig else Decimal("0")
    return mahnlogik.Config(
        mwst_satz=satz,
        mwst_nr=str(cd.mwst_nr or ""),
        firma=str(cd.company_name or "") or "Treuhandbüro Ivanova",
        iban=str(cd.iban or ""),
        kontakt=str(cd.email or ""),
    )


def offene_rechnungen(stichtag: date):
    """Rechnungen, die zum Stichtag überfällig sein können.

    `payment_status` wird nur bei save() berechnet und kann veraltet sein. Deshalb wird
    hier nicht auf UEBERFAELLIG gefiltert, sondern nach Fälligkeit; die genaue Prüfung
    (offener Betrag > 0) macht `mahnlogik.pruefe`.
    """
    return (
        Invoice.objects.filter(due_date__lt=stichtag)
        .exclude(payment_status__in=["BEZAHLT", "STORNIERT"])
        .select_related("client")
        .prefetch_related("mahnungen")
    )


def zu_rechnung(inv: Invoice) -> mahnlogik.Rechnung:
    return mahnlogik.Rechnung(
        nummer=inv.invoice_number,
        kunde=inv.client.name,
        rechnungsdatum=inv.invoice_date,
        faelligkeit=inv.due_date,
        brutto=Decimal(inv.amount),
        bezahlt=Decimal(inv.paid_amount or 0),
        mahnungen=[(m.stufe, m.datum) for m in inv.mahnungen.all()],
        mahnsperre=inv.mahnsperre,
        quelle=inv,
    )


def vorschau(stichtag: date, cfg: mahnlogik.Config | None = None) -> list[mahnlogik.Ergebnis]:
    """Trockenlauf: was wäre zum Stichtag fällig? Schreibt nichts."""
    cfg = cfg or config_aus_firmendaten()
    return mahnlogik.mahnlauf([zu_rechnung(i) for i in offene_rechnungen(stichtag)], stichtag, cfg)


def erzeuge_mahnung(e: mahnlogik.Ergebnis, user=None) -> Mahnung | None:
    """Speichert die Mahnung zu einem Ergebnis. Gibt None zurück, wenn es sie schon gibt."""
    if e.aktion != "mahnen":
        return None
    try:
        with transaction.atomic():
            return Mahnung.objects.create(
                invoice=e.rechnung.quelle,
                stufe=e.stufe.nr,
                datum=e.stichtag,
                zahlungsfrist=e.zahlungsfrist,
                offener_betrag=e.offen,
                zins_tage=e.zins_tage,
                verzugszins=e.zins,
                gebuehren=e.gebuehren,
                gebuehren_mwst=e.gebuehren_mwst,
                total=e.total,
                erstellt_von=user if getattr(user, "is_authenticated", False) else None,
            )
    except IntegrityError:
        return None  # doppelter Lauf: (Rechnung, Stufe) existiert bereits


def mahnlauf_ausfuehren(stichtag: date, user=None, nur_rechnungen: list[int] | None = None):
    """Erzeugt alle fälligen Mahnungen. Gibt (erzeugt, offen_fuer_betreibung) zurück."""
    cfg = config_aus_firmendaten()
    erzeugt, betreibung = [], []
    for e in vorschau(stichtag, cfg):
        if nur_rechnungen is not None and e.rechnung.quelle.pk not in nur_rechnungen:
            continue
        if e.aktion == "betreibung_pruefen":
            betreibung.append(e)
        elif (m := erzeuge_mahnung(e, user)):
            erzeugt.append(m)
    return erzeugt, betreibung
