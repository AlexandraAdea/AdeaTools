from django.db import models

from adeacore.models import PayrollRecord


class WageTypeCategory(models.TextChoices):
    GRUNDLOHN = "GRUNDLOHN", "Grundlohn"
    ZULAGE = "ZULAGE", "Zulage"
    FAMILIENZULAGE = "FAMILIENZULAGE", "Familienzuschlag"
    SPESEN = "SPESEN", "Spesen"
    SACHLEISTUNG = "SACHLEISTUNG", "Sachleistung"
    KORREKTUR = "KORREKTUR", "Korrektur"
    SONSTIGES = "SONSTIGES", "Sonstiges"


class WageType(models.Model):
    code = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=255)
    category = models.CharField(
        max_length=20,
        choices=WageTypeCategory.choices,
        default=WageTypeCategory.GRUNDLOHN,
    )
    description = models.TextField(blank=True)

    is_lohnwirksam = models.BooleanField(default=True)
    ahv_relevant = models.BooleanField(default=True)
    alv_relevant = models.BooleanField(default=True)
    bvg_relevant = models.BooleanField(default=True)
    uv_relevant = models.BooleanField(default=True)
    qst_relevant = models.BooleanField(default=True)
    taxable = models.BooleanField(default=True)

    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["code"]

    def __str__(self):
        return f"{self.code} – {self.name}"


class PayrollItem(models.Model):
    payroll = models.ForeignKey(
        PayrollRecord,
        on_delete=models.CASCADE,
        related_name="items",
    )
    wage_type = models.ForeignKey(
        WageType,
        on_delete=models.PROTECT,
        related_name="items",
    )
    quantity = models.DecimalField(max_digits=8, decimal_places=2, default=1)
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Betrag pro Einheit oder Gesamtbetrag, je nach Lohnart.",
    )
    description = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ["payroll_id", "wage_type__code"]

    @property
    def total(self):
        return self.quantity * self.amount

    def __str__(self):
        return f"{self.payroll_id} – {self.wage_type.code} – {self.total}"


class KTGParameter(models.Model):
    """
    Konfigurierbare Parameter für die Krankentaggeldversicherung (KTG).
    Es sollte nur eine Instanz existieren (Singleton-Pattern).
    """
    ktg_rate_employee = models.DecimalField(
        max_digits=5,
        decimal_places=4,
        default=0,
        help_text="KTG-Beitragssatz Arbeitnehmer (z.B. 0.0150 für 1.5%)",
    )
    ktg_rate_employer = models.DecimalField(
        max_digits=5,
        decimal_places=4,
        default=0,
        help_text="KTG-Beitragssatz Arbeitgeber (z.B. 0.0150 für 1.5%)",
    )
    ktg_max_basis = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Maximale Bemessungsgrundlage (z.B. 148200.00 für Jahreslohn). Optional.",
    )

    class Meta:
        verbose_name = "KTG Parameter"
        verbose_name_plural = "KTG Parameter"

    def __str__(self):
        return "KTG Parameter"


class BVGParameter(models.Model):
    """
    Konfigurierbare Parameter für die berufliche Vorsorge (BVG, 2. Säule).
    Ein Datensatz pro Jahr.
    """
    year = models.IntegerField(
        default=2025,
        unique=True,
        help_text="Jahr für diese BVG-Parameter",
    )
    entry_threshold = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Eintrittsschwelle (Jahreslohn, unterhalb keine BVG-Pflicht)",
    )
    coordination_deduction = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Koordinationsabzug (jährlich)",
    )
    min_insured_salary = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Minimum versicherter Lohn (jährlich)",
    )
    max_insured_salary = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Maximum versicherter Lohn (jährlich)",
    )
    employee_rate = models.DecimalField(
        max_digits=5,
        decimal_places=4,
        help_text="BVG-Beitragssatz Arbeitnehmer (z.B. 0.0500 für 5%)",
    )
    employer_rate = models.DecimalField(
        max_digits=5,
        decimal_places=4,
        help_text="BVG-Beitragssatz Arbeitgeber (z.B. 0.0500 für 5%)",
    )

    class Meta:
        verbose_name = "BVG Parameter"
        verbose_name_plural = "BVG Parameter"
        ordering = ["-year"]

    def __str__(self):
        return f"BVG Parameter {self.year}"


class QSTParameter(models.Model):
    """
    Konfigurierbare Parameter für die Quellensteuer (QST).
    Ein Datensatz pro Jahr und Tarif.
    """
    year = models.IntegerField(
        help_text="Jahr für diese QST-Parameter",
    )
    tarif = models.CharField(
        max_length=5,
        help_text="QST-Tarif im Format [Familienstand][Kinder][Kirchensteuer], z.B. 'A0N' (alleinstehend, 0 Kinder, ohne Kirche), "
                  "'A0Y' (mit Kirche), 'B1N' (verheiratet, 1 Kind, ohne Kirche), 'B1Y' (mit Kirche). "
                  "Familienstand: A=alleinstehend, B=verheiratet. Kirchensteuer: N=nein, Y=ja.",
    )
    prozent = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="QST-Prozentsatz (z.B. 5.00 für 5%)",
    )
    fixbetrag = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="QST-Fixbetrag (hat Vorrang vor Prozentsatz)",
    )

    class Meta:
        verbose_name = "QST Parameter"
        verbose_name_plural = "QST Parameter"
        unique_together = ("year", "tarif")
        ordering = ["-year", "tarif"]

    def __str__(self):
        return f"QST Parameter {self.year} – {self.tarif}"


class FamilyAllowanceParameter(models.Model):
    """
    Konfigurierbare Parameter für Familienzulagen (Kinderzulage / Ausbildungszulage).
    Ein Datensatz pro Jahr.
    
    Diese Beträge werden von der Familienausgleichskasse (FAK) festgelegt und
    sind jährlich unterschiedlich. Sie werden dem Arbeitgeber gutgeschrieben
    und an den Mitarbeiter weitergegeben.
    
    Wichtig: Familienzulagen sind:
    - QST-relevant (steuerbar)
    - NICHT AHV/ALV/UVG/BVG/KTG-relevant
    - gehören zum Bruttolohn (steuerbar)
    """
    year = models.IntegerField(
        unique=True,
        help_text="Jahr für diese Familienzulagen-Parameter",
    )
    kinderzulage_betrag = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Jährlicher Betrag pro Kind (Kinderzulage) in CHF",
    )
    ausbildungszulage_betrag = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Jährlicher Betrag pro Kind in Ausbildung (Ausbildungszulage) in CHF",
    )
    monatlich_kinderzulage = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Monatlicher Betrag pro Kind (Kinderzulage) in CHF (wird automatisch berechnet: jährlich / 12)",
        editable=False,
    )
    monatlich_ausbildungszulage = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Monatlicher Betrag pro Kind in Ausbildung (Ausbildungszulage) in CHF (wird automatisch berechnet: jährlich / 12)",
        editable=False,
    )

    class Meta:
        verbose_name = "Familienzulagen Parameter"
        verbose_name_plural = "Familienzulagen Parameter"
        ordering = ["-year"]

    def __str__(self):
        return f"Familienzulagen Parameter {self.year}"

    def save(self, *args, **kwargs):
        from decimal import Decimal
        # Automatische Berechnung der monatlichen Beträge
        self.monatlich_kinderzulage = self.kinderzulage_betrag / Decimal("12")
        self.monatlich_ausbildungszulage = self.ausbildungszulage_betrag / Decimal("12")
        super().save(*args, **kwargs)
