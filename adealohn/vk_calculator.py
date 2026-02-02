from decimal import Decimal

from adeacore.money import round_to_5_rappen


class VKCalculator:
    """
    Berechnet VK (Verwaltungskosten) gemäss konfigurierten Parametern:
    - Konfigurierbar pro Jahr über VKParameter
    - AG-Beitrag vom Total AHV/IV/EO-Beitrag (AN + AG)
    - Wird vom Arbeitgeber bezahlt
    - Aktueller Satz (in % des AHV-Betrags) kann auf AHV-Rechnung gefunden werden
    """

    @classmethod
    def calculate_for_payroll(cls, payroll):
        """
        Berechnet VK für einen PayrollRecord.

        Args:
            payroll: PayrollRecord-Instanz (muss bereits AHV-Beiträge berechnet haben)

        Returns:
            dict mit:
                - vk_employer: Arbeitgeberbeitrag (gerundet auf 0.05)
        """
        from adealohn.models import VKParameter

        params = VKParameter.objects.filter(year=payroll.year).first()
        
        # Fallback auf Standardwert wenn keine Parameter gefunden
        if not params:
            rate_employer = Decimal("0.03")  # 3.0% Standard (gemäss Excel-Vorlage)
        else:
            rate_employer = params.rate_employer

        # Total AHV-Beitrag = AN + AG
        total_ahv = (payroll.ahv_employee or Decimal("0.00")) + (payroll.ahv_employer or Decimal("0.00"))

        # VK-Beitrag berechnen
        vk_employer_raw = total_ahv * rate_employer

        # Auf 0.05 CHF runden
        vk_employer = round_to_5_rappen(vk_employer_raw)

        return {
            "vk_employer": vk_employer,
        }
