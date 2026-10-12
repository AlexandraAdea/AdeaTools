"""Mahnlogik für AdeaRechnung, ohne Django-Abhängigkeit (leicht testbar).

``pruefe`` beantwortet für eine Rechnung und einen Stichtag: Ist eine Mahnung fällig,
welche Stufe, mit welchem Verzugszins und welchen Gebühren?

Rechtliche Einordnung (keine Rechtsberatung, bitte selbst gegenprüfen):
- Ist ein Verfalltag vereinbart (Fälligkeitsdatum auf der Rechnung), kommt der
  Schuldner nach Art. 102 Abs. 2 OR ohne Mahnung in Verzug.
- Verzugszins 5 % nach Art. 104 Abs. 1 OR, berechnet auf der offenen Hauptforderung
  (inkl. MWST). Kein Zinseszins (Art. 105 Abs. 3 OR), keine Verzinsung der Gebühren.
- Mahngebühren sind nur als Verzugsschaden bzw. bei vertraglicher Grundlage durchsetzbar.
  Pauschalen gehören in Auftragsbestätigung/AGB, nicht nur in die Rechnungsfusszeile.
- MWST: Mahnspesen gehören nach ESTV (MWST-Info 04, Ziff. 3.8.2.3) zum Entgelt und sind
  steuerbar, Verzugszinsen nach Art. 104 OR sind Schadenersatz und nicht steuerbar.
  Geprüft an der Fassung Stand 01.01.2010 der MWST-Info 04, bitte gegen die aktuelle
  Fassung der ESTV gegenprüfen.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, timedelta
from decimal import Decimal, ROUND_HALF_UP
from typing import Any

RAPPEN = Decimal("0.01")
FUENF_RAPPEN = Decimal("0.05")


def runde_005(betrag: Decimal) -> Decimal:
    """Rundet auf 5 Rappen (kaufmännisch)."""
    return (betrag / FUENF_RAPPEN).quantize(Decimal("1"), ROUND_HALF_UP) * FUENF_RAPPEN


@dataclass(frozen=True)
class Stufe:
    nr: int
    name: str
    # Stufe 1: Tage nach Fälligkeit. Ab Stufe 2: Tage nach dem Datum der Vorstufe.
    wartetage: int
    frist_tage: int
    gebuehr: Decimal  # Bruttobetrag inkl. MWST (sofern MWST-pflichtig)
    betreibung_androhen: bool = False


STANDARD_STUFEN: tuple[Stufe, ...] = (
    Stufe(1, "Zahlungserinnerung", wartetage=5, frist_tage=10, gebuehr=Decimal("20.00")),
    Stufe(2, "1. Mahnung", wartetage=10, frist_tage=10, gebuehr=Decimal("20.00")),
    Stufe(3, "Letzte Mahnung", wartetage=10, frist_tage=10, gebuehr=Decimal("20.00"),
          betreibung_androhen=True),
)


@dataclass(frozen=True)
class Config:
    zinssatz: Decimal = Decimal("0.05")
    # "rechnung": Zins ab (Rechnungsdatum + zins_nach_tage), Lesart der Fusszeile
    #             "ab dem 30. Tag", für den Kunden günstiger.
    # "faelligkeit": Zins ab Fälligkeitsdatum + zins_nach_tage (rechtlich frühester Zeitpunkt
    #             bei Zinsbeginn 0 Tage, Art. 102 Abs. 2 / 104 OR).
    zins_beginn: str = "rechnung"
    zins_nach_tage: int = 30
    stufen: tuple[Stufe, ...] = STANDARD_STUFEN
    # Tage nach Ablauf der Frist der letzten Mahnung, bis "Betreibung prüfen" gemeldet wird.
    betreibung_nach_tage: int = 0
    mwst_satz: Decimal = Decimal("0.081")  # 0 = nicht MWST-pflichtig
    mwst_nr: str = ""
    firma: str = "Treuhandbüro Ivanova"
    iban: str = ""
    kontakt: str = ""


@dataclass
class Rechnung:
    nummer: str
    kunde: str
    rechnungsdatum: date
    faelligkeit: date
    brutto: Decimal
    bezahlt: Decimal = Decimal("0")
    # Bereits erzeugte Mahnungen: (Stufennummer, Datum)
    mahnungen: list[tuple[int, date]] = field(default_factory=list)
    mahnsperre: bool = False  # Streitfall, Stundung, Ratenzahlung vereinbart
    quelle: Any = field(default=None, repr=False, compare=False)  # z.B. das Invoice-Objekt


@dataclass
class Ergebnis:
    rechnung: Rechnung
    aktion: str  # "mahnen" | "betreibung_pruefen"
    stufe: Stufe | None
    stichtag: date
    tage_ueberfaellig: int
    offen: Decimal
    zins_tage: int
    zins: Decimal
    gebuehren: Decimal  # brutto, inkl. MWST
    total: Decimal
    zahlungsfrist: date | None
    gebuehren_netto: Decimal = Decimal("0.00")
    gebuehren_mwst: Decimal = Decimal("0.00")


def mwst_aufteilen(brutto: Decimal, cfg: Config) -> tuple[Decimal, Decimal]:
    """Zerlegt einen Bruttobetrag in (netto, MWST)."""
    netto = (brutto / (1 + cfg.mwst_satz)).quantize(RAPPEN, ROUND_HALF_UP)
    return netto, brutto - netto


def zins_beginn_datum(rechnungsdatum: date, faelligkeit: date, cfg: Config) -> date:
    basis = rechnungsdatum if cfg.zins_beginn == "rechnung" else faelligkeit
    return basis + timedelta(days=cfg.zins_nach_tage)


def berechne_zins(offen: Decimal, tage: int, cfg: Config) -> Decimal:
    if tage <= 0 or offen <= 0:
        return Decimal("0.00")
    return (offen * cfg.zinssatz * Decimal(tage) / Decimal(365)).quantize(RAPPEN, ROUND_HALF_UP)


def pruefe(r: Rechnung, stichtag: date, cfg: Config = Config()) -> Ergebnis | None:
    """Gibt ein Ergebnis zurück, wenn zum Stichtag etwas zu tun ist, sonst None."""
    offen = (r.brutto - r.bezahlt).quantize(RAPPEN)
    if offen <= 0 or r.mahnsperre:
        return None
    if stichtag <= r.faelligkeit:
        return None

    bisher = max((nr for nr, _ in r.mahnungen), default=0)
    letzte_datum = max((d for _, d in r.mahnungen), default=None)
    ueberfaellig = (stichtag - r.faelligkeit).days

    zins_start = zins_beginn_datum(r.rechnungsdatum, r.faelligkeit, cfg)
    zins_tage = max(0, (stichtag - zins_start).days)
    zins = berechne_zins(offen, zins_tage, cfg)

    stufen = {s.nr: s for s in cfg.stufen}
    letzte_stufe = max(stufen)

    if bisher >= letzte_stufe:
        s_letzt = stufen[letzte_stufe]
        grenze = letzte_datum + timedelta(days=s_letzt.frist_tage + cfg.betreibung_nach_tage)
        if stichtag <= grenze:
            return None
        gebuehren = sum((s.gebuehr for s in cfg.stufen), Decimal("0"))
        g_netto, g_mwst = mwst_aufteilen(gebuehren, cfg)
        return Ergebnis(r, "betreibung_pruefen", None, stichtag, ueberfaellig, offen,
                        zins_tage, zins, gebuehren, runde_005(offen + zins + gebuehren), None,
                        g_netto, g_mwst)

    naechste = stufen[bisher + 1]
    faellig_ab = (r.faelligkeit if bisher == 0 else letzte_datum) + timedelta(days=naechste.wartetage)
    if stichtag < faellig_ab:
        return None

    gebuehren = sum((s.gebuehr for s in cfg.stufen if s.nr <= naechste.nr), Decimal("0"))
    g_netto, g_mwst = mwst_aufteilen(gebuehren, cfg)
    return Ergebnis(r, "mahnen", naechste, stichtag, ueberfaellig, offen, zins_tage, zins,
                    gebuehren, runde_005(offen + zins + gebuehren),
                    stichtag + timedelta(days=naechste.frist_tage), g_netto, g_mwst)


def mahnlauf(rechnungen: list[Rechnung], stichtag: date, cfg: Config = Config()) -> list[Ergebnis]:
    ergebnisse = [e for r in rechnungen if (e := pruefe(r, stichtag, cfg))]
    return sorted(ergebnisse, key=lambda e: (e.aktion, -e.tage_ueberfaellig, e.rechnung.nummer))


# ---------------------------------------------------------------- Formatierung / Texte

def chf(x: Decimal) -> str:
    return f"CHF {x:,.2f}".replace(",", "’")


def d(x: date) -> str:
    return x.strftime("%d.%m.%Y")


def satz_text(cfg: Config) -> str:
    return f"{cfg.mwst_satz * 100:.1f}".rstrip("0").rstrip(".")


def stufentexte(stufe: Stufe, nummer: str, rechnungsdatum: date, faelligkeit: date,
                zahlungsfrist: date) -> tuple[str, str]:
    """(Einleitung, Schlusssatz) einer Mahnung, Sie-Form, Schweizer Rechtschreibung."""
    if stufe.nr == 1:
        return (
            f"unsere Rechnung {nummer} vom {d(rechnungsdatum)} war am {d(faelligkeit)} zur Zahlung fällig. "
            "Wir konnten bis heute keinen Zahlungseingang feststellen. Möglicherweise hat sich Ihre "
            "Zahlung mit diesem Schreiben gekreuzt, dann betrachten Sie es bitte als gegenstandslos.",
            f"Wir bitten Sie, den Gesamtbetrag bis {d(zahlungsfrist)} zu überweisen.",
        )
    if stufe.betreibung_androhen:
        return (
            f"die Rechnung {nummer} ist trotz Zahlungserinnerung und Mahnung nicht beglichen worden.",
            f"Wir setzen Ihnen letztmals Frist bis {d(zahlungsfrist)}. Nach unbenütztem Ablauf leiten wir "
            "ohne weitere Ankündigung die Betreibung ein. Die dadurch entstehenden Kosten gehen zu Ihren Lasten.",
        )
    return (
        f"trotz unserer Zahlungserinnerung ist die Rechnung {nummer} weiterhin offen. Sie befinden "
        "sich im Zahlungsverzug.",
        f"Bitte überweisen Sie den Gesamtbetrag bis {d(zahlungsfrist)}.",
    )


def betragszeilen(*, nummer: str, rechnungsdatum: date, faelligkeit: date, offen: Decimal,
                  zins: Decimal, zins_tage: int, zins_ab: date, gebuehren: Decimal,
                  gebuehren_mwst: Decimal, total: Decimal, stufe_nr: int,
                  cfg: Config) -> list[tuple[str, str]]:
    """Beschriftung und Betrag je Zeile der Aufstellung (für Text und PDF)."""
    zeilen = [(f"Rechnung {nummer} vom {d(rechnungsdatum)}, fällig am {d(faelligkeit)}", chf(offen))]
    if zins > 0:
        zeilen.append((f"Verzugszins 5 % p.a. ab {d(zins_ab)} ({zins_tage} Tage)", chf(zins)))
    hinweis = f" (darin MWST {satz_text(cfg)} %: {chf(gebuehren_mwst)})" if cfg.mwst_satz > 0 else ""
    if stufe_nr == 1:
        zeilen.append((f"Mahngebühr{hinweis}", chf(gebuehren)))
    else:
        zeilen.append((f"Mahngebühren, bisherige Stufen inkl. dieser{hinweis}", chf(gebuehren)))
    zeilen.append(("Total", chf(total)))
    return zeilen


def schreiben(e: Ergebnis, cfg: Config = Config()) -> str:
    """Mahntext als Klartext (z. B. für E-Mail-Versand)."""
    if e.aktion != "mahnen" or e.stufe is None:
        raise ValueError("Für 'betreibung_pruefen' wird kein Mahntext erzeugt.")
    r, s = e.rechnung, e.stufe
    einleitung, schluss = stufentexte(s, r.nummer, r.rechnungsdatum, r.faelligkeit, e.zahlungsfrist)
    zeilen = betragszeilen(
        nummer=r.nummer, rechnungsdatum=r.rechnungsdatum, faelligkeit=r.faelligkeit, offen=e.offen,
        zins=e.zins, zins_tage=e.zins_tage, zins_ab=zins_beginn_datum(r.rechnungsdatum, r.faelligkeit, cfg),
        gebuehren=e.gebuehren, gebuehren_mwst=e.gebuehren_mwst, total=e.total, stufe_nr=s.nr, cfg=cfg)
    tabelle = "\n".join(f"{label}: {betrag}" for label, betrag in zeilen)
    zahlung = f"Zahlung auf IBAN {cfg.iban}, Empfänger {cfg.firma}, Referenz {r.nummer}.\n" if cfg.iban else ""
    kontakt = f"Bei Fragen erreichen Sie uns unter {cfg.kontakt}.\n" if cfg.kontakt else ""
    mwst = f"\nMWST-Nr. {cfg.mwst_nr}\n" if cfg.mwst_nr else ""
    return (
        f"{s.name}, Rechnung {r.nummer}\n\nGuten Tag\n\n{einleitung}\n\n{tabelle}\n\n{schluss}\n\n"
        f"{zahlung}{kontakt}\nFreundliche Grüsse\n{cfg.firma}\n{mwst}"
    )
