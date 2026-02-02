from decimal import Decimal
from typing import TYPE_CHECKING

from adeacore.money import round_to_5_rappen

if TYPE_CHECKING:
    from adeacore.models import PayrollRecord


class ALVCalculator:
    """
    Berechnet ALV gemäss konfigurierten Parametern:
    - Beitragssätze konfigurierbar pro Jahr über ALVParameter
    - Nur auf Löhne bis Max-Basis pro Jahr
    - Rentner zahlen keine ALV
    """

    def calculate_for_payroll(self, payroll: "PayrollRecord") -> dict:
        from decimal import Decimal
        from adealohn.models import ALVParameter

        params = ALVParameter.objects.filter(year=payroll.year).first()
        
        # Fallback auf Standardwerte wenn keine Parameter gefunden
        if not params:
            rate_employee = Decimal("0.011")  # 1.1% Standard
            rate_employer = Decimal("0.011")  # 1.1% Standard
            max_year = Decimal("148200.00")
        else:
            rate_employee = params.rate_employee
            rate_employer = params.rate_employer
            max_year = params.max_annual_insured_salary

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
        alv_employee_raw = effective_basis * rate_employee
        alv_employer_raw = effective_basis * rate_employer

        alv_employee = round_to_5_rappen(alv_employee_raw)
        alv_employer = round_to_5_rappen(alv_employer_raw)

        return {
            "alv_effective_basis": effective_basis,
            "alv_employee": alv_employee,
            "alv_employer": alv_employer,
        }



