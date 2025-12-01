from decimal import Decimal, ROUND_HALF_UP


class UVGCalculator:
    """
    Berechnet UVG (Unfallversicherungsgesetz) gemäss Schweizer Recht 2025:
    - BU (Berufsunfall): Arbeitgeberbeitrag
    - NBU (Nichtberufsunfall): Arbeitnehmerbeitrag, nur bei >8h/Woche
    - Lohnobergrenze: 148'200 CHF/Jahr (12'350 CHF/Monat)
    """

    RATE_BU_EMPLOYER = Decimal("0.00")  # Platzhalter, wird später von Versicherer definiert
    RATE_NBU_EMPLOYEE = Decimal("0.00")  # Platzhalter, wird später definiert

    MAX_ANNUAL_INSURED_SALARY = Decimal("148200.00")

    def get_month_cap(self):
        return self.MAX_ANNUAL_INSURED_SALARY / Decimal("12")

    def calculate_for_payroll(self, payroll):
        from decimal import Decimal

        basis = payroll.uv_basis or Decimal("0.00")
        employee = getattr(payroll, "employee", None)

        # YTD-Logik: Berechne YTD-Basis + aktuelle Basis
        ytd_basis = getattr(employee, "uvg_ytd_basis", Decimal("0.00")) or Decimal("0.00")
        ytd_basis = Decimal(str(ytd_basis))
        max_year = self.MAX_ANNUAL_INSURED_SALARY
        
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
        bu_employer_raw = effective_basis * self.RATE_BU_EMPLOYER
        bu_employer = (bu_employer_raw / Decimal("0.05")).quantize(
            Decimal("1"), rounding=ROUND_HALF_UP
        ) * Decimal("0.05")
        bu_employee = Decimal("0.00")

        # NBU: nur wenn Pflicht (>8h/Woche)
        if getattr(employee, "nbu_pflichtig", False):
            nbu_employee_raw = effective_basis * self.RATE_NBU_EMPLOYEE
            nbu_employee = (nbu_employee_raw / Decimal("0.05")).quantize(
                Decimal("1"), rounding=ROUND_HALF_UP
            ) * Decimal("0.05")
        else:
            nbu_employee = Decimal("0.00")

        return {
            "uvg_effective_basis": effective_basis,
            "bu_employer": bu_employer,
            "bu_employee": bu_employee,
            "nbu_employee": nbu_employee,
        }



