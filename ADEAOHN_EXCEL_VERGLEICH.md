# AdeaLohn vs. Excel-Vorlage - Vergleichsanalyse

**Datum:** 16. Januar 2026  
**Basis:** Excel-Vorlage "Lohnbuchhaltung einfach. By Run my Accounts AG"

---

## ✅ KORREKT IMPLEMENTIERT

### 1. AHV (Alters- und Hinterlassenenversicherung)
- **Excel:** 5.3% AN + 5.3% AG = 10.6% Total
- **AdeaLohn:** ✅ `AHVCalculator.RATE_EMPLOYEE = 0.053`, `RATE_EMPLOYER = 0.053`
- **Rentnerfreibetrag:** ✅ 1'400 CHF/Monat (nur bei Rentnern)
- **Rundung:** ✅ Auf 5 Rappen

### 2. ALV1 (Arbeitslosenversicherung, 1. Stufe)
- **Excel:** 1.1% AN + 1.1% AG = 2.2% Total, bis 148'200 CHF/Jahr
- **AdeaLohn:** ✅ `ALVCalculator.RATE_EMPLOYEE = 0.011`, `RATE_EMPLOYER = 0.011`
- **Kappung:** ✅ YTD-Logik bis 148'200 CHF
- **Rentner:** ✅ Keine ALV für Rentner
- **Rundung:** ✅ Auf 5 Rappen

### 3. ALV2 (Arbeitslosenversicherung, 2. Stufe)
- **Excel:** 0.0% (ab 01.01.2023 entfällt)
- **AdeaLohn:** ✅ Nicht implementiert (korrekt, da entfällt)

### 4. BVG (Berufliche Vorsorge, 2. Säule)
- **Excel:** Aus Police/Liste entnehmen
- **AdeaLohn:** ✅ Konfigurierbar über `BVGParameter` (pro Jahr)
- **YTD-Logik:** ✅ Jahreslohn = YTD + aktueller Monat
- **Koordinationsabzug:** ✅ Implementiert
- **Korridore:** ✅ Min/Max versicherter Lohn
- **Rundung:** ✅ Auf 5 Rappen

### 5. KTG (Krankentaggeldversicherung)
- **Excel:** 0.5% AN + 0.5% AG = 1.0% Total, bis 300'000 CHF
- **AdeaLohn:** ✅ Konfigurierbar über `KTGParameter`
- **Max-Basis:** ✅ Optional konfigurierbar (ktg_max_basis)
- **Rundung:** ✅ Auf 5 Rappen

### 6. Familienzulagen (FAK)
- **Excel:** 1.0% AG Beitrag (Familienausgleichskasse)
- **AdeaLohn:** ✅ `FamilyAllowanceParameter` für Beträge
- **Hinweis:** FAK-Beträge werden als Zulagen erfasst (Kinderzulage/Ausbildungszulage), nicht als AG-Beitrag

### 7. QST (Quellensteuer)
- **Excel:** Prozentsatz pro Monat (variabel)
- **AdeaLohn:** ✅ Jetzt in `PayrollRecord` (monatlich variabel)
- **Rundung:** ✅ Auf 5 Rappen

### 8. Rundung
- **Excel:** "Lohnabrechnung auf 5 Rp. runden"
- **AdeaLohn:** ✅ `round_to_5_rappen()` in allen Calculators

### 9. NBU-Pflicht
- **Excel:** "Weniger als 8 Arbeitstunden pro Woche" → keine NBU
- **AdeaLohn:** ✅ Validierung ab 8h/Woche implementiert

---

## ⚠️ FEHLENDE ODER UNVOLLSTÄNDIGE KOMPONENTEN

### 1. FAK-Beitrag (Familienausgleichskasse)
- **Offizielle Tabelle:** 1.025% AG Beitrag (vom Bruttolohn)
- **Excel-Vorlage:** 1.0% AG (vereinfacht/gerundet)
- **AdeaLohn:** ❌ Nicht als AG-Beitrag implementiert
- **Status:** Familienzulagen werden als Zulagen erfasst, aber FAK-Beitrag fehlt
- **Empfehlung:** FAK-Beitrag als separater AG-Beitrag hinzufügen (**1.025% vom Bruttolohn**, nicht 1.0%!)

### 2. VK (Verwaltungskosten)
- **Offizielle Tabelle:** 5.0% AG (vom **Total AHV/IV/EO-Beitrag**, nicht nur AG-Anteil!)
- **Excel-Vorlage:** 3.0% AG (veraltet oder falsch)
- **AdeaLohn:** ❌ Nicht implementiert
- **Empfehlung:** VK als separater AG-Beitrag hinzufügen (**5.0% vom Total AHV-Beitrag** = 5.0% × (AHV-AN + AHV-AG))

### 3. BU/NBU Raten (UVG)
- **Excel:** 
  - BU: 0.644% AG, bis 148'200 CHF
  - NBUV: 2.3% AN, bis 148'200 CHF (nur ab 8h/Woche)
- **AdeaLohn:** ⚠️ Raten sind Platzhalter (0.00)
  - `UVGCalculator.RATE_BU_EMPLOYER = 0.00`
  - `UVGCalculator.RATE_NBU_EMPLOYEE = 0.00`
- **Status:** Logik vorhanden, aber Raten müssen konfigurierbar sein
- **Empfehlung:** UVGParameter-Model erstellen (wie BVGParameter/KTGParameter)

### 4. Ferienentschädigung
- **Excel:** 8.33% (4 Wochen) oder 10.64% (5 Wochen) oder manuell (z.B. 11.00%)
- **AdeaLohn:** ❌ Nicht implementiert
- **Status:** Fehlt komplett - sollte automatisch auf Stundenlohn aufgeschlagen werden
- **Empfehlung:** Ferienentschädigung als automatischer Zuschlag bei Stundenlöhnen implementieren

---

## 📊 ZUSAMMENFASSUNG

### Implementiert (9/13):
✅ AHV (5.3% AN/AG)  
✅ ALV1 (1.1% AN/AG, bis 148'200)  
✅ ALV2 (entfällt, korrekt nicht implementiert)  
✅ BVG (konfigurierbar)  
✅ KTG (konfigurierbar)  
✅ Familienzulagen (Beträge)  
✅ QST (monatlich variabel)  
✅ Rundung (5 Rappen)  
✅ NBU-Pflicht (ab 8h/Woche)  

### Fehlend oder unvollständig (4/13):
❌ FAK-Beitrag (**1.025%** AG, nicht 1.0%!)  
❌ VK (**5.0%** AG vom **Total AHV-Beitrag**, nicht 3.0%!)  
⚠️ BU/NBU Raten (Platzhalter, müssen konfigurierbar sein)  
❌ Ferienentschädigung (8.33%/10.64% fehlt)  

---

## 🔧 EMPFOHLENE NÄCHSTE SCHRITTE

1. **UVGParameter-Model erstellen** (BU/NBU Raten konfigurierbar machen)
2. **FAK-Beitrag hinzufügen** (**1.025%** AG vom Bruttolohn - korrigiert!)
3. **VK (Verwaltungskosten) hinzufügen** (**5.0%** AG vom **Total AHV-Beitrag** - korrigiert!)
4. **Ferienentschädigung implementieren** (8.33%/10.64% für Stundenlöhne)

---

## ⚠️ KRITISCHE KORREKTUREN (basierend auf offizieller Tabelle)

**Quelle:** Offizielle Berechnungstabelle "Berechnung der Sozialversicherungsbeiträge"

### Korrigierte Werte:
- **FAK:** 1.025% (nicht 1.0% wie in Excel-Vorlage)
- **VK:** 5.0% vom **Total AHV-Beitrag** (nicht 3.0% vom AG-Anteil)
