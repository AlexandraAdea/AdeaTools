from decimal import Decimal

from adeacore.money import round_to_5_rappen


class UVGCalculator:
    """
    Berechnet UVG (Unfallversicherungsgesetz) gemäss Schweizer Recht 2025:
    - BU (Berufsunfall): Arbeitgeberbeitrag
    - NBU (Nichtberufsunfall): Arbeitnehmerbeitrag, nur bei >8h/Woche
    - Lohnobergrenze: 148'200 CHF/Jahr (12'350 CHF/Monat)
    """

    def calculate_for_payroll(self, payroll):
        from decimal import Decimal
        from adealohn.models import UVGParameter

        params = UVGParameter.objects.filter(year=payroll.year).first()

        if not params:
            return {
                "uvg_effective_basis": Decimal("0.00"),
                "bu_employer": Decimal("0.00"),
                "bu_employee": Decimal("0.00"),
                "nbu_employee": Decimal("0.00"),
            }

        basis = payroll.uv_basis or Decimal("0.00")
        employee = getattr(payroll, "employee", None)

        # YTD-Logik: Berechne YTD-Basis + aktuelle Basis
        ytd_basis = getattr(employee, "uvg_ytd_basis", Decimal("0.00")) or Decimal("0.00")
        ytd_basis = Decimal(str(ytd_basis))
        max_year = params.max_annual_insured_salary
        
        # Prüfe ob YTD-Basis bereits über Maximum liegt
        if ytd_basis >= max_year:
            # Bereits über Maximum, keine weitere Berechnung
            capped_current = Decimal("0.00")
        else:
            # Berechne wie viel noch möglich ist
            remaining = max_year - ytd_basis
            capped_current = min(basis, remaining)
        
        effective_basis = capped_current

        # BU: immer nur Arbeitgeber
        bu_employer_raw = effective_basis * params.bu_rate_employer
        bu_employer = round_to_5_rappen(bu_employer_raw)
        bu_employee = Decimal("0.00")

        # NBU: nur wenn Pflicht (>8h/Woche)
        if getattr(employee, "nbu_pflichtig", False):
            nbu_employee_raw = effective_basis * params.nbu_rate_employee
            nbu_employee = round_to_5_rappen(nbu_employee_raw)
        else:
            nbu_employee = Decimal("0.00")

        return {
            "uvg_effective_basis": effective_basis,
            "bu_employer": bu_employer,
            "bu_employee": bu_employee,
            "nbu_employee": nbu_employee,
        }



