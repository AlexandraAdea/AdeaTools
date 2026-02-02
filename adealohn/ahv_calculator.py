from decimal import Decimal

from adeacore.money import round_to_5_rappen


class AHVCalculator:
    """
    Berechnet AHV-Beiträge basierend auf der AHV-Basis eines PayrollRecords.
    Berücksichtigt Rentnerfreibetrag falls aktiviert.
    Verwendet AHVParameter für jährlich konfigurierbare Sätze.
    """

    @classmethod
    def calculate_for_payroll(cls, payroll):
        """
        Berechnet AHV-Beiträge für einen PayrollRecord.

        Args:
            payroll: PayrollRecord-Instanz

        Returns:
            dict mit:
                - ahv_effective_basis: Bemessungsgrundlage nach Freibetrag
                - ahv_employee: Arbeitnehmerbeitrag (gerundet auf 0.05)
                - ahv_employer: Arbeitgeberbeitrag (gerundet auf 0.05)
        """
        from adealohn.models import AHVParameter

        params = AHVParameter.objects.filter(year=payroll.year).first()
        
        # Fallback auf Standardwerte wenn keine Parameter gefunden
        if not params:
            rate_employee = Decimal("0.053")  # 5.3% Standard
            rate_employer = Decimal("0.053")  # 5.3% Standard
            rentner_freibetrag = Decimal("1400.00")
        else:
            rate_employee = params.rate_employee
            rate_employer = params.rate_employer
            rentner_freibetrag = params.rentner_freibetrag_monat

        basis = payroll.ahv_basis
        employee = payroll.employee

        # Rentnerfreibetrag anwenden
        if employee.is_rentner and employee.ahv_freibetrag_aktiv:
            effective_basis = max(basis - rentner_freibetrag, Decimal("0"))
        else:
            effective_basis = basis

        # AHV-Beiträge berechnen
        ahv_employee_raw = effective_basis * rate_employee
        ahv_employer_raw = effective_basis * rate_employer

        # Auf 0.05 CHF runden
        ahv_employee = round_to_5_rappen(ahv_employee_raw)
        ahv_employer = round_to_5_rappen(ahv_employer_raw)

        return {
            "ahv_effective_basis": effective_basis,
            "ahv_employee": ahv_employee,
            "ahv_employer": ahv_employer,
        }




