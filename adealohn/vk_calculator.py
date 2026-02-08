from decimal import Decimal

from adeacore.money import round_to_5_rappen
from .helpers import get_parameter_for_year, safe_decimal
from adealohn.models import VKParameter


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
        # Parameter mit Fallback laden (mit Caching)
        defaults = {
            "rate_employer": Decimal("0.03"),  # 3.0% Standard (gemäss Excel-Vorlage)
        }
        params = get_parameter_for_year(VKParameter, payroll.year, defaults=defaults)
        
        rate_employer = params.rate_employer if params else defaults["rate_employer"]

        # Total AHV-Beitrag = AN + AG
        total_ahv = safe_decimal(payroll.ahv_employee) + safe_decimal(payroll.ahv_employer)

        # VK-Beitrag berechnen
        vk_employer_raw = total_ahv * rate_employer

        # Auf 0.05 CHF runden
        vk_employer = round_to_5_rappen(vk_employer_raw)

        return {
            "vk_employer": vk_employer,
        }
