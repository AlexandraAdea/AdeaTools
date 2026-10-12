from django.conf import settings
from django.db import models


class Mahnung(models.Model):
    """
    Protokoll einer erzeugten Mahnung (Beträge und Termine zum Zeitpunkt des Mahnlaufs).

    Bewusst ohne Mahntext und ohne Adresse: Name und Anschrift des Mandanten sind in der
    Datenbank verschlüsselt und werden beim PDF-Druck aus dem Mandanten gelesen.
    """

    invoice = models.ForeignKey(
        "adeacore.Invoice",
        on_delete=models.CASCADE,
        related_name="mahnungen",
        verbose_name="Rechnung",
    )
    stufe = models.PositiveSmallIntegerField("Mahnstufe")
    datum = models.DateField("Mahndatum")
    zahlungsfrist = models.DateField("Zahlungsfrist")
    offener_betrag = models.DecimalField("Offener Betrag", max_digits=10, decimal_places=2)
    zins_tage = models.PositiveIntegerField("Zinstage", default=0)
    verzugszins = models.DecimalField("Verzugszins", max_digits=10, decimal_places=2)
    gebuehren = models.DecimalField(
        "Mahngebühren (brutto)", max_digits=10, decimal_places=2,
        help_text="Kumuliert über alle Stufen, inkl. MWST.",
    )
    gebuehren_mwst = models.DecimalField("Darin MWST", max_digits=10, decimal_places=2, default=0)
    total = models.DecimalField("Total", max_digits=10, decimal_places=2)
    versendet_am = models.DateField("Versendet am", null=True, blank=True)
    erstellt_von = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",
        verbose_name="Erstellt von",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Mahnung"
        verbose_name_plural = "Mahnungen"
        ordering = ["-datum", "-stufe"]
        constraints = [
            models.UniqueConstraint(fields=["invoice", "stufe"], name="uniq_mahnung_invoice_stufe"),
        ]

    def __str__(self):
        return f"Mahnung Stufe {self.stufe} zu {self.invoice.invoice_number} vom {self.datum:%d.%m.%Y}"
