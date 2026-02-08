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
            payroll.qst_abzug = Decimal("0.00")
            return

        # Basis bestimmen: qst_basis (bereits korrekt berechnet als ALV-Basis - AN-Sozialabzüge)
        # Fallback auf gross_salary nur wenn qst_basis nicht gesetzt
        basis = payroll.qst_basis if payroll.qst_basis and payroll.qst_basis > 0 else (payroll.bruttolohn or Decimal("0.00"))

        qst_amount = Decimal("0.00")

        # 2. Fixbetrag hat Vorrang (vom Employee)
        if employee.qst_fixbetrag:
            qst_amount = employee.qst_fixbetrag

        # 3. Dann Prozentsatz vom PayrollRecord (monatlich variabel)
        elif payroll.qst_prozent:
            qst_amount = basis * (payroll.qst_prozent / Decimal("100"))

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

        payroll.qst_abzug = qst_amount


