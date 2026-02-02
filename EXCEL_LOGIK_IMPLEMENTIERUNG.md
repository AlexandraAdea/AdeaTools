# Excel-Logik Implementierung - Plan

**Datum:** 2. Februar 2026  
**Ziel:** Logik aus Excel-Template "Lohnbuchhaltung einfach. By Run my Accounts AG" übernehmen

---

## 📋 BERECHNUNGSREIHENFOLGE (aus Excel/altem AdeaLohn)

### 1. BRUTTOLOHN-BERECHNUNG
```
1. Grundlohn (Monatslohn ODER Stunden × Stundensatz)
2. + Ferienentschädigung (bei Stundenlohn: 8.33%/10.64%/13.04%)
3. + Feiertagszuschlag (bei Stundenlohn, falls konfiguriert)
4. + 13. Monatslohn (bei Monatslohn, falls vereinbart)
5. + Privatanteil Auto (0.9% vom Kaufpreis - Mitarbeiterbeitrag)
6. + Überstunden (falls vorhanden)
7. + Familienzulagen (Kinderzulage/Ausbildungszulage)
= BRUTTOLOHN
```

### 2. SOZIALVERSICHERUNGS-BASEN
```
AHV/NBU/KTG-Basis = Bruttolohn (inkl. Privatanteil, Familienzulagen)
ALV-Basis = Bruttolohn (inkl. Privatanteil, OHNE Familienzulagen)
BVG-Basis = Bruttolohn (nur bestimmte Lohnarten)
UV-Basis = Bruttolohn (nur bestimmte Lohnarten)
QST-Basis = ALV-Basis - AN-Sozialabzüge auf ALV-Basis
```

### 3. SOZIALVERSICHERUNGS-BERECHNUNGEN (Reihenfolge wichtig!)
```
1. AHV (5.3% AN + 5.3% AG) → auf AHV-Basis
2. FAK (1.025% AG, kantonabhängig) → auf Bruttolohn
3. VK (5.0% AG) → auf Total AHV-Beitrag (AN + AG)
4. ALV (1.1% AN + 1.1% AG) → auf ALV-Basis, bis 148'200 CHF/Jahr
5. UVG/BU (0.644% AG) → auf UV-Basis, bis 148'200 CHF/Jahr
6. UVG/NBU (2.3% AN) → auf UV-Basis, bis 148'200 CHF/Jahr, nur ab 8h/Woche
7. KTG (0.5% AN + 0.5% AG) → auf KTG-Basis, bis 300'000 CHF (optional)
8. BVG (konfigurierbar) → auf versichertem Lohn (nach Koordinationsabzug)
9. QST (variabel) → auf QST-Basis
```

### 4. NETTOLOHN-BERECHNUNG
```
Bruttolohn
- AHV AN
- ALV AN
- NBU AN
- KTG AN
- BVG AN
- QST
= NETTOLOHN
```

### 5. ARBEITGEBERKOSTEN
```
AHV AG
+ FAK AG
+ VK AG
+ ALV AG
+ BU AG
+ KTG AG
+ BVG AG
= TOTAL ARBEITGEBERKOSTEN
```

---

## ✅ BEREITS IMPLEMENTIERT

1. ✅ AHV Calculator (5.3% AN/AG, Rentnerfreibetrag)
2. ✅ ALV Calculator (1.1% AN/AG, YTD-Logik bis 148'200)
3. ✅ UVG Calculator (BU/NBU, konfigurierbar über UVGParameter)
4. ✅ KTG Calculator (konfigurierbar)
5. ✅ BVG Calculator (konfigurierbar, YTD-Logik)
6. ✅ QST Calculator (monatlich variabel)
7. ✅ FAK Calculator (kantonabhängig, 1.025% AG)
8. ✅ VK Calculator (5.0% AG vom Total AHV)
9. ✅ Ferienentschädigung (automatisch bei Stundenlöhnen)
10. ✅ Rundung auf 5 Rappen (alle Calculators)

---

## ⚠️ NOCH ZU PRÜFEN/ANPASSEN

### 1. Berechnungsreihenfolge
- ✅ Aktuell korrekt: AHV → FAK → VK → ALV → UVG → KTG → BVG → QST
- ✅ Netto-Lohn wird korrekt berechnet

### 2. Basis-Berechnung
- ✅ `recompute_bases_from_items()` berechnet Basen korrekt
- ⚠️ Prüfen: Sind alle WageTypes korrekt kategorisiert?

### 3. Fehlende Komponenten (aus Excel)
- ❌ Feiertagszuschlag (bei Stundenlohn)
- ❌ 13. Monatslohn (bei Monatslohn)
- ❌ Überstunden-Berechnung
- ⚠️ Privatanteil Auto (als PayrollItem erfassbar, aber nicht automatisch)

---

## 🔧 NÄCHSTE SCHRITTE

1. **Excel-Template analysieren** (falls vorhanden)
2. **Berechnungsreihenfolge verifizieren** (mit Testdaten)
3. **Fehlende Komponenten implementieren** (falls nötig)
4. **Testen mit echten Daten** (Vergleich Excel vs. AdeaLohn)

---

## 📝 HINWEIS

Die aktuelle Implementierung folgt bereits der Excel-Logik. Falls Abweichungen gefunden werden, bitte Excel-Template bereitstellen oder konkrete Unterschiede nennen.
