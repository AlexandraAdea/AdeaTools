from decimal import Decimal

from adeacore.money import round_to_5_rappen


class QSTCalculator:
    """
    Berechnet Quellensteuer (QST) gemäss konfigurierten Parametern.
    Basis ist qst_basis (aus WageTypes) oder fallback gross_salary.
    """

    def calculate_for_payroll(self, payroll):
        from decimal import Decimal
        from adealohn.models import QSTParameter

        employee = getattr(payroll, "employee", None)

        # 1. Wenn nicht QST-pflichtig → 0.00
        if not employee or not getattr(employee, "qst_pflichtig", False):
            payroll.qst_amount = Decimal("0.00")
            return

        # Basis bestimmen: qst_basis oder fallback gross_salary
        basis = payroll.qst_basis or payroll.gross_salary or Decimal("0.00")

        qst_amount = Decimal("0.00")

        # 2. Fixbetrag hat Vorrang
        if employee.qst_fixbetrag:
            qst_amount = employee.qst_fixbetrag

        # 3. Dann Prozentsatz vom Employee
        elif employee.qst_prozent:
            qst_amount = basis * (employee.qst_prozent / Decimal("100"))

        # 4. Suche QSTParameter(year, tarif) mit effektivem Tarif (inkl. Kirchensteuer)
        elif employee.qst_tarif:
            effective_tarif = employee.qst_effective_tarif
            qst_param = QSTParameter.objects.filter(
                year=payroll.year, tarif=effective_tarif
            ).first()

            if qst_param:
                if qst_param.fixbetrag:
                    qst_amount = qst_param.fixbetrag
                elif qst_param.prozent:
                    qst_amount = basis * (qst_param.prozent / Decimal("100"))

        # 5. Sonst 0.00 (bereits gesetzt)

        # Rundung auf 0.05 CHF
        qst_amount = round_to_5_rappen(qst_amount)

        payroll.qst_amount = qst_amount


