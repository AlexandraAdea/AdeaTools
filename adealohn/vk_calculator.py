from decimal import Decimal

from adeacore.money import round_to_5_rappen


class VKCalculator:
    """
    Berechnet VK (Verwaltungskosten) gemäss Schweizer Recht:
    - 5.0% AG vom Total AHV/IV/EO-Beitrag (AN + AG)
    - Wird vom Arbeitgeber bezahlt
    """

    RATE_EMPLOYER = Decimal("0.05")  # 5.0% Arbeitgeber

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
        # Total AHV-Beitrag = AN + AG
        total_ahv = (payroll.ahv_employee or Decimal("0.00")) + (payroll.ahv_employer or Decimal("0.00"))

        # VK-Beitrag berechnen
        vk_employer_raw = total_ahv * cls.RATE_EMPLOYER

        # Auf 0.05 CHF runden
        vk_employer = round_to_5_rappen(vk_employer_raw)

        return {
            "vk_employer": vk_employer,
        }
