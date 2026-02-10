"""Quick smoke test for adea_payroll package."""
import sys
sys.path.insert(0, ".")

from decimal import Decimal
from adea_payroll import (
    berechne_lohnlauf, pruefe_plausibilitaet,
    Firmendaten, Mitarbeitende, Lohnstamm,
    rappen, proz,
)

# Test 1: Rounding
assert rappen(Decimal("10.03")) == Decimal("10.05"), "rappen failed"
assert rappen(Decimal("10.02")) == Decimal("10.00"), "rappen failed"
print("✅ Test 1: Rundung OK")

# Test 2: Prozent
assert proz(Decimal("6000"), Decimal("5.3")) == Decimal("318.00"), f"proz failed: {proz(Decimal('6000'), Decimal('5.3'))}"
print("✅ Test 2: Prozent OK")

# Test 3: Full payroll
firma = Firmendaten(
    bu_satz_ag=Decimal("0.5"),
    nbu_satz_an=Decimal("1.2"),
)
ma = Mitarbeitende(vorname="Max", nachname="Muster")
ls = Lohnstamm(monatslohn=Decimal("6000"))

abr = berechne_lohnlauf(ma, ls, firma, 1, 2025)
assert abr.grundlohn == Decimal("6000"), f"Grundlohn: {abr.grundlohn}"
assert abr.ahv_an == Decimal("318.00"), f"AHV AN: {abr.ahv_an}"
assert abr.netto > 0, f"Netto should be positive: {abr.netto}"
print(f"✅ Test 3: Lohnlauf OK (Grundlohn={abr.grundlohn}, AHV={abr.ahv_an}, Netto={abr.netto})")

# Test 4: Validation
ergebnisse = pruefe_plausibilitaet(ma, ls, abr, firma, 1, 2025)
assert len(ergebnisse) > 0, "Should have at least one result"
print(f"✅ Test 4: Plausibilität OK ({len(ergebnisse)} Ergebnisse)")

print("\n🎉 ALL TESTS PASSED")
