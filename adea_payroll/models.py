"""
Datenmodelle für AdeaLohn 1.0
Definiert die vollständige Datenstruktur für eine Schweizer Lohnsoftware
"""

from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from enum import Enum
from typing import Optional, List, Dict
from uuid import UUID, uuid4


# ============================================================================
# ENUMERATIONEN
# ============================================================================

class Lohnart(Enum):
    """Art des Lohns"""
    MONATSLOHN = "Monatslohn"
    STUNDENLOHN = "Stundenlohn"


class LohnBasisTyp(Enum):
    """Typ der Lohnbasis für Monatslohn"""
    HUNDERT_PROZENT = "100_PROZENT"  # Vertragslohn ist 100%-Lohn
    EFF_EFFEKTIV = "EFF_EFFEKTIV"  # Vertragslohn ist effektiver Lohn


class Dreizehnter(Enum):
    """Modell für 13. Monatslohn"""
    NOVEMBER_100 = "100% im November"
    DEZEMBER_100 = "100% im Dezember"
    JUNI_NOVEMBER_50_50 = "50% Juni / 50% November"
    KEIN_13 = "Kein 13. Monatslohn"


class Ferienwochen(Enum):
    """Anzahl Ferienwochen für Ferienzuschlag-Berechnung"""
    VIER_WOCHEN = "4 Wochen"  # 8.33% Zuschlag
    FUENF_WOCHEN = "5 Wochen"  # 10.64% Zuschlag (Standard)
    SECHS_WOCHEN = "6 Wochen"  # 13.04% Zuschlag


class Zivilstand(Enum):
    """Zivilstand"""
    LEDIG = "ledig"
    VERHEIRATET = "verheiratet"
    GESCHIEDEN = "geschieden"
    VERWITWET = "verwitwet"
    GETRENNT = "getrennt"


class Konfession(Enum):
    """Religionszugehörigkeit für QST"""
    REFORMIERT = "reformiert"
    ROEMISCH_KATHOLISCH = "römisch-katholisch"
    CHRISTKATHOLISCH = "christkatholisch"
    ANDERE = "andere"
    KONFESSIONSLOS = "konfessionslos"


class QSTTarif(Enum):
    """QST-Tarife"""
    A = "A - Alleinstehend"
    B = "B - Verheiratet (Einverdiener)"
    C = "C - Verheiratet (Doppelverdiener)"
    D = "D - Alleinerziehend"
    H = "H - Nebenerwerb"


class Branche(Enum):
    """Betriebstätigkeit / Branche"""
    COIFFEUR = "Coiffeur"
    KOSMETIK_BEAUTY = "Kosmetik / Beauty"
    GASTRO = "Gastro"
    REINIGUNG = "Reinigung"
    BAU_HANDWERK = "Bau / Handwerk"
    SPITEX_BETREUUNG = "Spitex / Betreuung"
    BUERO_ADMINISTRATION = "Büro / Administration"
    IT_DIENSTLEISTUNGEN = "IT / Dienstleistungen"
    VERKAUF_RETAIL = "Verkauf / Retail"
    SONSTIGES = "Sonstiges"


class GAVStatus(Enum):
    """GAV-Status des Betriebs"""
    KEIN_GAV = "Kein GAV"
    AVE_GAV = "AVE-GAV (zwingend)"
    NICHT_AVE_GAV = "Nicht-AVE-GAV (optional)"


class LohnlaufStatus(Enum):
    """Status eines Lohnlaufs"""
    ENTWURF = "entwurf"  # Lohnlauf kann bearbeitet werden
    ABGESCHLOSSEN = "abgeschlossen"  # Lohnlauf ist gesperrt (sperre)
    AUSGEZAHLT = "ausgezahlt"  # Lohnlauf wurde ausgezahlt


class KTGKategorie(Enum):
    """KTG-Kategorie für Mitarbeitende"""
    NICHT_VERSICHERT = "Nicht versichert"
    GESCHAEFTSLEITUNG = "Geschäftsleitung"
    MITARBEITENDE = "Mitarbeitende"


class KTGVerteilung(Enum):
    """Verteilung der KTG-Kosten zwischen AN und AG"""
    AN_100 = "100% Arbeitnehmer"
    AG_100 = "100% Arbeitgeber"
    HALB_HALB = "50% / 50%"


class FamilienzulageTyp(Enum):
    """Typ der Familienzulage"""
    KINDERZULAGE = "Kinderzulage"
    AUSBILDUNGSZULAGE = "Ausbildungszulage"


# ============================================================================
# 1. FIRMENDATEN
# ============================================================================

@dataclass
class Firmendaten:
    """Stammdaten des Unternehmens"""
    # Identifikation
    id: UUID = field(default_factory=uuid4)

    # Firmenadresse
    firmenname: str = ""
    strasse: str = ""
    plz: str = ""
    ort: str = ""
    kanton: str = ""
    
    # Kontakt (NEU)
    email: str = ""
    telefon: str = ""
    hr_name: str = ""  # HR-Verantwortlicher
    hr_email: str = ""

    # Amtliche Nummern
    uid: str = ""  # Unternehmens-Identifikationsnummer
    iban: str = ""

    # Betriebstätigkeit / Branche
    branche: Optional[Branche] = None
    gav_status: GAVStatus = GAVStatus.KEIN_GAV

    # Versicherungssätze
    bu_satz_ag: Decimal = Decimal("0.0")  # Berufsunfall (Arbeitgeber)
    nbu_satz_an: Decimal = Decimal("0.0")  # Nichtberufsunfall (Arbeitnehmer)

    # KTG-Konfiguration
    ktg_verteilung: KTGVerteilung = KTGVerteilung.HALB_HALB
    ktg_saetze_pro_kategorie: Dict[str, Decimal] = field(default_factory=lambda: {
        "NICHT_VERSICHERT": Decimal("0.0"),
        "GESCHAEFTSLEITUNG": Decimal("0.0"),
        "MITARBEITENDE": Decimal("0.0")
    })

    # Standard-Zuschläge (in Prozent)
    feiertag_zuschlag: Decimal = Decimal("0.0")
    ferien_zuschlag: Decimal = Decimal("10.64")  # Standard für 4 Wochen Ferien

    erstellt_am: date = field(default_factory=date.today)


# ============================================================================
# 2. MITARBEITENDE
# ============================================================================

@dataclass
class QSTDaten:
    """Daten für Quellensteuer"""
    qst_pflichtig: bool = False
    tarif: Optional[QSTTarif] = None  # A, B, C, H, D
    wohnkanton: str = ""
    konfession: Optional[Konfession] = None
    kinder_anzahl: int = 0

    # Gemeinde-Informationen
    gemeinde: Optional[str] = None  # Name der Gemeinde
    bfs_code: Optional[int] = None  # BFS-Code (Gemeinde-Nummer)

    # Manueller QST-Prozentsatz (vereinfachte Lösung)
    qst_prozentsatz: Optional[Decimal] = None  # % vom Nettolohn

    # Für Tarif C (Doppelverdiener) / Tarif B (Einverdiener)
    partner_erwerbstaetig: Optional[bool] = None  # NEU: True/False/None für Auto-Tarif
    einkommen_ehepartner_jahr: Optional[Decimal] = None


@dataclass
class Mitarbeitende:
    """Stammdaten eines Mitarbeiters / einer Mitarbeiterin"""
    # Identifikation
    id: UUID = field(default_factory=uuid4)
    personalnummer: str = ""

    # Personendaten
    vorname: str = ""
    nachname: str = ""
    geburtsdatum: Optional[date] = None
    ahv_nummer: str = ""  # Format: 756.XXXX.XXXX.XX

    # Adresse
    strasse: str = ""
    plz: str = ""
    ort: str = ""
    land: str = "CH"  # NEU: ISO-Code (CH, DE, FR, AT) für Grenzgänger
    
    # Kontakt (NEU)
    email: str = ""
    telefon: str = ""
    mobil: str = ""

    # Zivilstand
    zivilstand: Zivilstand = Zivilstand.LEDIG

    # QST-Daten
    qst_daten: QSTDaten = field(default_factory=QSTDaten)

    # Beschäftigung
    eintrittsdatum: Optional[date] = None
    austrittsdatum: Optional[date] = None

    # Tätigkeit / Branche
    taetigkeit_branche: str = ""  # z.B. "Coiffeur", "Gastro"

    # KTG-Kategorie
    ktg_kategorie: KTGKategorie = KTGKategorie.MITARBEITENDE
    
    # Altersrentner (ab Referenzalter: 65 Jahre, Frauen 64J+3M in 2025)
    ist_altersrentner: bool = False  # Manuell oder automatisch aus Geburtsdatum
    verzicht_ahv_freibetrag: bool = False  # NEU seit AHV 21: Verzicht auf Freibetrag CHF 16'800

    # Familienzulagen (Liste von Zulagen pro Mitarbeiter)
    familienzulagen: List['Familienzulage'] = field(default_factory=list)

    # Status
    aktiv: bool = True
    erstellt_am: date = field(default_factory=date.today)


# ============================================================================
# 2b. FAMILIENZULAGEN
# ============================================================================

@dataclass
class Familienzulage:
    """
    Familienzulage für einen Mitarbeiter
    Basierend auf SVA-Entscheiden, ohne Namen der Kinder
    """
    # Identifikation
    id: UUID = field(default_factory=uuid4)
    mitarbeiter_id: UUID = field(default_factory=uuid4)
    
    # Zulagendaten
    betrag: Decimal = Decimal("0.0")  # Monatlicher Betrag in CHF
    typ: FamilienzulageTyp = FamilienzulageTyp.KINDERZULAGE
    
    # Gültigkeitszeitraum
    gueltig_ab: date = field(default_factory=date.today)
    gueltig_bis: Optional[date] = None  # None = aktuell gültig
    
    erstellt_am: date = field(default_factory=date.today)


# ============================================================================
# 3. LOHNSTAMMDATEN (mit Historie)
# ============================================================================

@dataclass
class Lohnstamm:
    """
    Lohnstammdaten für einen Mitarbeiter
    Unterstützt Historie mit gültig_ab / gültig_bis
    """
    # Identifikation
    id: UUID = field(default_factory=uuid4)
    mitarbeiter_id: UUID = field(default_factory=uuid4)

    # Lohnart
    lohnart: Lohnart = Lohnart.MONATSLOHN

    # Grundlohn
    monatslohn: Optional[Decimal] = None  # nur bei Lohnart MONATSLOHN
    stundenlohn: Optional[Decimal] = None  # nur bei Lohnart STUNDENLOHN

    # Beschäftigungsgrad
    beschaeftigungsgrad: Decimal = Decimal("100.0")  # in Prozent (Pensum)
    
    # Lohnbasis-Typ (nur bei Monatslohn)
    lohn_basis_typ: Optional[LohnBasisTyp] = LohnBasisTyp.HUNDERT_PROZENT  # 100_PROZENT oder EFF_EFFEKTIV

    # 13. Monatslohn (nur bei Monatslohn)
    dreizehnter_modell: Dreizehnter = Dreizehnter.NOVEMBER_100

    # Zuschläge (nur bei Stundenlohn)
    ferienwochen: Ferienwochen = Ferienwochen.FUENF_WOCHEN  # Anzahl Ferienwochen (4, 5 oder 6)
    ferien_zuschlag: Decimal = Decimal("10.64")  # in Prozent (wird automatisch aus ferienwochen berechnet, kann manuell überschrieben werden)
    feiertag_zuschlag: Decimal = Decimal("0.0")  # in Prozent
    
    # Überstunden-Zuschläge (für Monatslohn und Stundenlohn)
    ueberstunden_zuschlag_normal: Decimal = Decimal("25.0")  # Standard: 25% (OR), kann 0% sein für 1:1-Vergütung
    ueberstunden_zuschlag_nacht: Decimal = Decimal("50.0")  # Standard: 50% (Nacht/Sonntag/Feiertag), kann 0% sein

    # Gültigkeit (Historie)
    gueltig_ab: date = field(default_factory=date.today)
    gueltig_bis: Optional[date] = None  # None = aktuell gültig

    # BVG-Beiträge (individuell pro Person aus Versicherungsvertrag)
    bvg_ag_beitrag: Optional[Decimal] = None  # Arbeitgeberbeitrag pro Monat (CHF)
    bvg_an_beitrag: Optional[Decimal] = None  # Arbeitnehmerbeitrag pro Monat (CHF)
    bvg_gueltig_ab: Optional[date] = None     # Gültig ab Datum

    # Pauschalspesen (Tagespauschalen) - GAV-kompatibel, vor allem Bau/Handwerk
    pauschalspesen_pro_tag: Optional[Decimal] = None  # Pauschalspesen pro Tag (CHF), z.B. 20.00 CHF/Tag

    # Privatanteil Fahrzeug (gemäss ESTV)
    privatanteil_auto_aktiv: bool = False
    auto_preis: Optional[Decimal] = None  # Fahrzeugpreis (exkl. MWST)
    auto_mitarbeiter_beitrag_monat: Decimal = Decimal("0.0")  # Mitarbeiterbeitrag pro Monat (reduziert Privatanteil)

    # Automatisch berechnete Felder (werden von Berechnung gefüllt)
    bvg_pflichtig: bool = False  # Nur für Warnungen (BVG wird manuell eingegeben)
    alv_pflichtig: bool = True

    erstellt_am: date = field(default_factory=date.today)


# ============================================================================
# 4. LOHNLAUF / PAYROLL
# ============================================================================

@dataclass
class Sozialabzuege:
    """Sozialversicherungsabzüge eines Lohnlaufs"""
    # AHV/IV/EO (kombiniert)
    ahv_iv_eo_basis: Decimal = Decimal("0.0")
    ahv_iv_eo_satz_an: Decimal = Decimal("5.3")  # Standard 5.3% AN
    ahv_iv_eo_betrag_an: Decimal = Decimal("0.0")

    # ALV (Arbeitslosenversicherung) - ALV2 entfernt
    alv_basis: Decimal = Decimal("0.0")
    alv_satz_an: Decimal = Decimal("1.1")  # Standard 1.1% AN
    alv_betrag_an: Decimal = Decimal("0.0")

    # BVG (Pensionskasse)
    bvg_basis: Decimal = Decimal("0.0")
    bvg_satz_an: Decimal = Decimal("0.0")  # abhängig von Alter
    bvg_betrag_an: Decimal = Decimal("0.0")

    # NBU (Nichtberufsunfall)
    nbu_basis: Decimal = Decimal("0.0")
    nbu_satz_an: Decimal = Decimal("0.0")  # aus Firmendaten
    nbu_betrag_an: Decimal = Decimal("0.0")

    # KTG (Krankentaggeld)
    ktg_basis: Decimal = Decimal("0.0")
    ktg_satz_an: Decimal = Decimal("0.0")  # aus Firmendaten
    ktg_betrag_an: Decimal = Decimal("0.0")

    # QST (Quellensteuer)
    qst_basis: Decimal = Decimal("0.0")
    qst_satz: Decimal = Decimal("0.0")
    qst_betrag: Decimal = Decimal("0.0")


@dataclass
class Lohnkomponenten:
    """Alle Lohnbestandteile eines Lohnlaufs"""
    # Grundlohn
    grundlohn: Decimal = Decimal("0.0")

    # Bei Stundenlohn
    stunden: Decimal = Decimal("0.0")
    stundenlohn: Decimal = Decimal("0.0")

    # Zuschläge
    ferienzuschlag_betrag: Decimal = Decimal("0.0")
    feiertagszuschlag_betrag: Decimal = Decimal("0.0")

    # 13. Monatslohn (anteilig in diesem Monat)
    dreizehnter_betrag: Decimal = Decimal("0.0")

    # Zusätzliche Zahlungen
    spesen: Decimal = Decimal("0.0")
    bonus: Decimal = Decimal("0.0")
    gratifikation: Decimal = Decimal("0.0")

    # Abzüge (nicht Sozialabzüge)
    privatanteil: Decimal = Decimal("0.0")

    # Bruttolohn = Summe aller Lohnkomponenten
    bruttolohn: Decimal = Decimal("0.0")


@dataclass
class Lohnlauf:
    """Ein monatlicher Lohnlauf für einen Mitarbeiter"""
    # Identifikation
    id: UUID = field(default_factory=uuid4)
    mitarbeiter_id: UUID = field(default_factory=uuid4)
    lohnstamm_id: UUID = field(default_factory=uuid4)  # Welcher Lohnstamm gilt?

    # Abrechnungsperiode
    jahr: int = 0
    monat: int = 0  # 1-12

    # Gearbeitete Stunden (nur bei Stundenlohn)
    stunden_gearbeitet: Decimal = Decimal("0.0")

    # Lohnkomponenten
    komponenten: Lohnkomponenten = field(default_factory=Lohnkomponenten)

    # Sozialabzüge
    abzuege: Sozialabzuege = field(default_factory=Sozialabzuege)

    # Nettolohn
    nettolohn: Decimal = Decimal("0.0")

    # Auszahlung
    auszahlungsbetrag: Decimal = Decimal("0.0")
    auszahlungsdatum: Optional[date] = None

    # PDF
    pdf_pfad: Optional[str] = None

    # Status
    status: str = "entwurf"  # entwurf, abgeschlossen, ausgezahlt

    erstellt_am: date = field(default_factory=date.today)
    berechnet_am: Optional[date] = None


@dataclass
class Lohnabrechnung:
    """
    Vereinfachte Lohnabrechnung für einen Mitarbeiter (v1 - nur Monatslohn)
    Enthält Bruttolohn, alle Abzüge, Nettolohn und Arbeitgeber-Kosten
    """
    # Identifikation
    id: UUID = field(default_factory=uuid4)
    mitarbeiter_id: UUID = field(default_factory=uuid4)

    # Abrechnungsperiode
    monat: int = 1  # 1-12
    jahr: int = 2025
    erstellt_am: date = field(default_factory=date.today)

    # Lohnbasis
    grundlohn: Decimal = Decimal("0.0")  # Monatslohn oder Stundenlohn * Stunden (inkl. Ferienzuschlag)
    stunden_gearbeitet: Decimal = Decimal("0.0")  # Gearbeitete Stunden (nur bei Stundenlohn, manuell pro Abrechnung)
    ferienzuschlag_betrag: Decimal = Decimal("0.0")  # Ferienzuschlag-Betrag (nur bei Stundenlohn)
    feiertagszuschlag_betrag: Decimal = Decimal("0.0")  # Feiertagszuschlag-Betrag (nur bei Stundenlohn)
    dreizehnter_betrag: Decimal = Decimal("0.0")  # 13. Monatslohn-Betrag (bei Monatslohn: separat, bei Stundenlohn: als Zuschlag)
    bonus: Decimal = Decimal("0.0")  # Bonus-Zahlung (sozialversicherungspflichtig, manuell pro Abrechnung)
    
    # Überstunden (sozialversicherungspflichtig, manuell pro Abrechnung)
    ueberstunden_normal: Decimal = Decimal("0.0")  # Anzahl normale Überstunden (mit 25% Zuschlag)
    ueberstunden_normal_zuschlag: Decimal = Decimal("25.0")  # Zuschlag % (aus Lohnstamm, kann überschrieben werden)
    ueberstunden_nacht: Decimal = Decimal("0.0")  # Anzahl Nacht-/Sonntags-/Feiertagsüberstunden (mit 50% Zuschlag)
    ueberstunden_nacht_zuschlag: Decimal = Decimal("50.0")  # Zuschlag % (aus Lohnstamm, kann überschrieben werden)
    ueberstunden_betrag_total: Decimal = Decimal("0.0")  # Berechnet: Total Überstunden-Entschädigung
    
    privatanteil_auto_brutto: Decimal = Decimal("0.0")  # 0.9% vom Kaufpreis/Monat (Brutto)
    privatanteil_auto_mitarbeiter_beitrag: Decimal = Decimal("0.0")  # Mitarbeiterbeitrag pro Monat
    privatanteil_auto: Decimal = Decimal("0.0")  # Netto-Privatanteil (Brutto - Mitarbeiterbeitrag, wird zum Bruttolohn addiert)
    familienzulagen: Decimal = Decimal("0.0")  # Familienzulagen (automatisch berechnet, für AHV/NBU/KTG-Basis)
    familienzulagen_nachzahlung: Decimal = Decimal("0.0")  # Nachzahlung/Rückforderung Familienzulagen (manuell, kann negativ sein)
    familienzulagen_nachzahlung_von_monat: Optional[int] = None  # Nachzahlung für Periode: von Monat (1-12)
    familienzulagen_nachzahlung_von_jahr: Optional[int] = None  # Nachzahlung für Periode: von Jahr
    familienzulagen_nachzahlung_bis_monat: Optional[int] = None  # Nachzahlung für Periode: bis Monat (1-12)
    familienzulagen_nachzahlung_bis_jahr: Optional[int] = None  # Nachzahlung für Periode: bis Jahr
    basis: Decimal = Decimal("0.0")  # grundlohn + privatanteil_auto + familienzulagen + familienzulagen_nachzahlung (für AHV/NBU/KTG)
    alv_basis: Decimal = Decimal("0.0")  # grundlohn + privatanteil_auto (für ALV, ohne Familienzulagen)
    qst_basis: Decimal = Decimal("0.0")  # ALV-Basis - AN-Sozialabzüge auf ALV-Basis

    # Arbeitnehmer-Abzüge (AN)
    ahv_an: Decimal = Decimal("0.0")  # AHV/IV/EO 5.3%
    alv1_an: Decimal = Decimal("0.0")  # ALV 1.1% bis Cap
    alv2_an: Decimal = Decimal("0.0")  # ALV 0.5% ab Cap
    nbu_an: Decimal = Decimal("0.0")  # Nichtberufsunfall (aus Firmendaten)
    ktg_an: Decimal = Decimal("0.0")  # Krankentaggeld-Anteil AN
    bvg_an: Decimal = Decimal("0.0")  # Pensionskasse AN (manuell eingegeben)
    qst: Decimal = Decimal("0.0")  # Quellensteuer (manuell eingegeben)

    sozialabzuege_total: Decimal = Decimal("0.0")  # Summe aller AN-Abzüge
    
    # Spesen (AHV/ALV/NBU/BU/BVG/QST-frei, werden zum Netto addiert)
    effektive_spesen_betrag: Decimal = Decimal("0.0")  # Effektive Spesen (Belegspesen) - manuell pro Abrechnung
    pauschalspesen_pro_tag: Decimal = Decimal("0.0")  # Pauschalspesen pro Tag (aus Lohnstamm)
    arbeitstage_pauschalspesen: int = 0  # Anzahl Arbeitstage für Pauschalspesen (manuell pro Abrechnung)
    pauschalspesen_total: Decimal = Decimal("0.0")  # Berechnet: pauschalspesen_pro_tag * arbeitstage_pauschalspesen
    
    netto: Decimal = Decimal("0.0")  # basis - sozialabzuege_total + effektive_spesen_betrag + pauschalspesen_total

    # Arbeitgeber-Kosten (AG)
    ahv_ag: Decimal = Decimal("0.0")  # AHV/IV/EO 5.3%
    alv1_ag: Decimal = Decimal("0.0")  # ALV 1.1% bis Cap (seit 2023: keine Beiträge mehr über Cap)
    alv2_ag: Decimal = Decimal("0.0")  # ALV ab Cap (seit 2023: immer 0.0, keine Beiträge mehr über Cap)
    bu_ag: Decimal = Decimal("0.0")  # Berufsunfall (aus Firmendaten)
    ktg_ag: Decimal = Decimal("0.0")  # Krankentaggeld-Anteil AG
    bvg_ag: Decimal = Decimal("0.0")  # Pensionskasse AG (manuell eingegeben)

    ag_kosten_total: Decimal = Decimal("0.0")  # Summe aller AG-Kosten
    ag_kosten_manuell: Optional[Decimal] = None  # Manuell eingegebene AG-Kosten (überschreibt automatische Berechnung)
    
    # Anteilige Berechnung (Eintritt/Austritt im Monat)
    anteiliger_lohn: bool = False  # True wenn Lohn anteilig berechnet wurde (bei Eintritt/Austritt im Monat)
    
    # Status und Sperre
    status: LohnlaufStatus = LohnlaufStatus.ENTWURF  # Status des Lohnlaufs (entwurf, abgeschlossen, ausgezahlt)
    gesperrt_am: Optional[date] = None  # Datum, wann der Lohnlauf gesperrt wurde
    gesperrt_von: Optional[str] = None  # Benutzer, der den Lohnlauf gesperrt hat


# ============================================================================
# 5. PDF-DATENSTRUKTUR
# ============================================================================

@dataclass
class PDFFirmenkopf:
    """Firmendaten für PDF-Kopfzeile"""
    firmenname: str
    strasse: str
    plz_ort: str
    uid: str
    iban: str


@dataclass
class PDFMitarbeiterBlock:
    """Mitarbeiterdaten für PDF"""
    personalnummer: str
    vorname: str
    nachname: str
    strasse: str
    plz_ort: str
    ahv_nummer: str


@dataclass
class PDFLohnzeile:
    """Eine Zeile in der Lohnabrechnung"""
    bezeichnung: str
    menge: str  # z.B. "160.0 Std" oder ""
    ansatz: str  # z.B. "25.00 CHF/Std" oder ""
    betrag: Decimal


@dataclass
class PDFAbzugszeile:
    """Eine Abzugszeile"""
    bezeichnung: str
    basis: Decimal
    satz: Decimal  # in Prozent
    betrag: Decimal


@dataclass
class LohnabrechnungPDF:
    """
    Vollständige Datenstruktur für eine PDF-Lohnabrechnung
    Diese Struktur wird an den PDF-Generator übergeben
    """
    # Kopfdaten
    firmenkopf: PDFFirmenkopf
    mitarbeiter: PDFMitarbeiterBlock

    # Periode
    abrechnungsperiode: str  # z.B. "November 2024"

    # Lohnkomponenten
    lohnzeilen: List[PDFLohnzeile] = field(default_factory=list)

    # Zwischensummen
    bruttolohn: Decimal = Decimal("0.0")

    # Abzüge
    abzugszeilen: List[PDFAbzugszeile] = field(default_factory=list)
    total_abzuege: Decimal = Decimal("0.0")

    # Netto
    nettolohn: Decimal = Decimal("0.0")

    # Auszahlung
    auszahlungsbetrag: Decimal = Decimal("0.0")
    auszahlungsdatum: Optional[date] = None
    iban_auszahlung: str = ""

    # GAV-Hinweis (falls relevant)
    gav_hinweis: Optional[str] = None

    # Erstellungsdatum
    erstellt_am: date = field(default_factory=date.today)


# ============================================================================
# HELPER-FUNKTIONEN
# ============================================================================

def ermittle_gav_status(branche: Optional[Branche]) -> GAVStatus:
    """
    Ermittelt den GAV-Status basierend auf der Branche

    Args:
        branche: Betriebstätigkeit / Branche

    Returns:
        GAVStatus (AVE-GAV, Nicht-AVE-GAV oder Kein GAV)
    """
    if branche is None:
        return GAVStatus.KEIN_GAV

    # Branchen mit allgemeinverbindlichem GAV (AVE-GAV = zwingend)
    ave_gav_branchen = {
        Branche.COIFFEUR,
        Branche.GASTRO,
        Branche.REINIGUNG,
        Branche.BAU_HANDWERK,
    }

    # Branchen mit nicht-allgemeinverbindlichem GAV (optional)
    nicht_ave_gav_branchen = {
        Branche.SPITEX_BETREUUNG,
        Branche.KOSMETIK_BEAUTY,
    }

    if branche in ave_gav_branchen:
        return GAVStatus.AVE_GAV
    elif branche in nicht_ave_gav_branchen:
        return GAVStatus.NICHT_AVE_GAV
    else:
        return GAVStatus.KEIN_GAV


def get_aktueller_lohnstamm(mitarbeiter_id: UUID, lohnstaemme: List[Lohnstamm],
                           stichtag: date = None) -> Optional[Lohnstamm]:
    """
    Ermittelt den aktuell gültigen Lohnstamm für einen Mitarbeiter

    Args:
        mitarbeiter_id: ID des Mitarbeiters
        lohnstaemme: Liste aller Lohnstämme
        stichtag: Datum für Gültigkeit (default: heute)

    Returns:
        Aktuell gültiger Lohnstamm oder None
    """
    if stichtag is None:
        stichtag = date.today()

    gueltige = [
        ls for ls in lohnstaemme
        if ls.mitarbeiter_id == mitarbeiter_id
        and ls.gueltig_ab <= stichtag
        and (ls.gueltig_bis is None or ls.gueltig_bis >= stichtag)
    ]

    # Neueste zuerst
    gueltige.sort(key=lambda x: x.gueltig_ab, reverse=True)

    return gueltige[0] if gueltige else None
