from decimal import Decimal
from typing import TYPE_CHECKING

from adeacore.money import round_to_5_rappen

if TYPE_CHECKING:
    from adeacore.models import PayrollRecord


class ALVCalculator:
    """
    Berechnet ALV gemäss Schweizer Recht 2025:
    - Beitragssatz Arbeitnehmer: 1.1 %
    - Beitragssatz Arbeitgeber: 1.1 %
    - Nur auf Löhne bis 148'200 CHF pro Jahr
    - Rentner zahlen keine ALV
    """

    RATE_EMPLOYEE = Decimal("0.011")
    RATE_EMPLOYER = Decimal("0.011")
    MAX_ANNUAL_INSURED_SALARY = Decimal("148200.00")

    def calculate_for_payroll(self, payroll: "PayrollRecord") -> dict:
        from decimal import Decimal

        basis = payroll.alv_basis or Decimal("0.00")
        employee = getattr(payroll, "employee", None)
        is_rentner = getattr(employee, "is_rentner", False)

        # Keine ALV für Rentner
        if is_rentner:
            return {
                "alv_effective_basis": Decimal("0.00"),
                "alv_employee": Decimal("0.00"),
                "alv_employer": Decimal("0.00"),
            }

        # YTD-Logik: Berechne YTD-Basis + aktuelle Basis
        ytd_basis = getattr(employee, "alv_ytd_basis", Decimal("0.00")) or Decimal("0.00")
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

        # ALV-Beiträge berechnen und auf 0.05 CHF runden
        alv_employee_raw = effective_basis * self.RATE_EMPLOYEE
        alv_employer_raw = effective_basis * self.RATE_EMPLOYER

        alv_employee = round_to_5_rappen(alv_employee_raw)
        alv_employer = round_to_5_rappen(alv_employer_raw)

        return {
            "alv_effective_basis": effective_basis,
            "alv_employee": alv_employee,
            "alv_employer": alv_employer,
        }



