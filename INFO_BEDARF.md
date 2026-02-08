# Informationen die ich für die Verbesserungen brauche

## 🎯 Für Integrationstests

### 1. Konkrete Test-Szenarien aus der Praxis

**Bitte geben Sie mir 2-3 reale Beispiele:**

#### Beispiel 1: Standard-Monatslohn mit Familienzulage
```
Mitarbeiter: [Name]
Monatslohn: [Betrag] CHF
Familienzulage: [Betrag] CHF (für [Anzahl] Kinder)
Privatanteil Auto: [Betrag] CHF (falls vorhanden)
BVG AN: [Betrag] CHF
BVG AG: [Betrag] CHF

Erwartetes Ergebnis:
- Bruttolohn: [Betrag] CHF (OHNE Familienzulage)
- Spesen und Zulagen: [Betrag] CHF (Familienzulage)
- Abzüge Sozialversicherungen: [Betrag] CHF
- Auszahlung: [Betrag] CHF
```

#### Beispiel 2: Stundenlohn mit Überstunden
```
Mitarbeiter: [Name]
Stundensatz: [Betrag] CHF/h
Arbeitsstunden: [Anzahl] h
Überstunden: [Anzahl] h
Familienzulage: [Betrag] CHF
BVG AN: [Betrag] CHF
BVG AG: [Betrag] CHF

Erwartetes Ergebnis:
- Bruttolohn: [Betrag] CHF
- ...
```

#### Beispiel 3: Rentner mit Freibetrag
```
Mitarbeiter: [Name] (Rentner)
Monatslohn: [Betrag] CHF
AHV-Freibetrag aktiv: Ja/Nein

Erwartetes Ergebnis:
- AHV-Basis: [Betrag] CHF (mit Freibetrag)
- ALV: 0.00 CHF (Rentner zahlen keine ALV)
```

### 2. Edge-Cases die getestet werden sollen

**Welche speziellen Situationen treten bei Ihnen auf?**

- [ ] Mitarbeiter unter BVG-Eintrittsschwelle (< 22'032 CHF/Jahr)
- [ ] Mitarbeiter über ALV/UVG-Maximum (> 148'200 CHF/Jahr)
- [ ] Teilzeit-Mitarbeiter (< 8h/Woche → keine NBU)
- [ ] Grenzgänger (QST-pflichtig)
- [ ] Mitarbeiter mit mehreren Privatanteilen
- [ ] Nachzahlungen von Familienzulagen
- [ ] Wechsel der BVG-Beiträge während des Jahres
- [ ] Andere? _______________

### 3. Vergleichswerte für Validierung

**Haben Sie Vergleichswerte aus Abacus/Sage?**

- Beispiel-Lohnabrechnung aus Abacus/Sage als PDF oder Screenshot
- Oder: Excel-Datei mit Berechnungen
- Oder: Manuelle Berechnungen mit Formeln

## 📋 Für Geschäftslogik-Dokumentation

### 4. Klärung offener Fragen

#### Familienzulagen:
- ✅ **Bestätigt:** Familienzulagen gehören NICHT zum Bruttolohn (Durchlaufender Posten SVA)
- ❓ **Frage:** Gibt es Ausnahmen? Z.B. bei bestimmten Lohnarten?
- ❓ **Frage:** Werden Familienzulagen immer separat als "Spesen und Zulagen" angezeigt?

#### BVG-Beiträge:
- ✅ **Bestätigt:** BVG wird manuell erfasst (AN + AG)
- ❓ **Frage:** Gibt es Fälle wo automatische Berechnung gewünscht ist?
- ❓ **Frage:** Wie werden BVG-Beiträge bei Teilzeit-Mitarbeitern gehandhabt?
- ❓ **Frage:** Was passiert wenn BVG-Beiträge während des Jahres wechseln?

#### Privatanteile:
- ✅ **Bestätigt:** Privatanteile gehören zum Bruttolohn, werden aber später abgezogen
- ❓ **Frage:** Gibt es verschiedene Arten von Privatanteilen? (Auto, Telefon, etc.)
- ❓ **Frage:** Werden Privatanteile bei der Sozialversicherungs-Basis berücksichtigt?

#### QST (Quellensteuer):
- ❓ **Frage:** Wie wird QST berechnet? (Prozentsatz, Tarif, Fixbetrag?)
- ❓ **Frage:** Gibt es monatliche Schwankungen bei Stundenlöhnen?

### 5. Regeln die dokumentiert werden sollen

**Welche Regeln sind für Sie am wichtigsten?**

- [ ] Was gehört zum Bruttolohn?
- [ ] Was sind "Durchlaufende Posten SVA"?
- [ ] Wie funktioniert die BVG-Berechnung?
- [ ] Wie werden YTD-Werte (Year-to-Date) gehandhabt?
- [ ] Wann werden YTD-Werte zurückgesetzt?
- [ ] Wie funktioniert die Rentner-Freibetrag-Logik?
- [ ] Andere? _______________

## 🔧 Für Code-Verbesserungen

### 6. Prioritäten

**Was ist für Sie am wichtigsten?**

1. [ ] Integrationstests für kritische Workflows
2. [ ] Geschäftslogik-Dokumentation
3. [ ] UI-Validierung (Warnungen bei falschen Eingaben)
4. [ ] Code-Review-Checkliste
5. [ ] Test-Daten für alle Edge-Cases

**Reihenfolge bitte nummerieren (1 = höchste Priorität)**

### 7. Workflows die getestet werden sollen

**Welche Workflows sind für Sie am kritischsten?**

- [ ] PayrollRecord erstellen → Items hinzufügen → Speichern → Berechnung prüfen
- [ ] Familienzulage hinzufügen → Prüfen dass sie NICHT im Bruttolohn ist
- [ ] BVG manuell erfassen → Prüfen dass Berechnung korrekt ist
- [ ] Print-View → Prüfen dass alle Werte korrekt angezeigt werden
- [ ] Rentner-Freibetrag → Prüfen dass AHV-Basis korrekt reduziert wird
- [ ] YTD-Reset im Januar → Prüfen dass Werte zurückgesetzt werden
- [ ] Andere? _______________

## 📊 Für Test-Daten

### 8. Beispiel-Daten

**Können Sie mir Beispiel-Daten geben?**

- [ ] Beispiel-Mitarbeiter (anonymisiert)
- [ ] Beispiel-PayrollRecord mit allen Lohnarten
- [ ] Beispiel-Berechnung mit erwarteten Werten
- [ ] Oder: Ich erstelle Test-Daten basierend auf Ihren Angaben

## 🎯 Nächste Schritte

**Sobald ich diese Informationen habe, kann ich:**

1. ✅ Integrationstests implementieren
2. ✅ Geschäftslogik-Dokumentation erstellen
3. ✅ UI-Validierung hinzufügen
4. ✅ Code-Review-Checkliste erstellen
5. ✅ Test-Daten generieren

**Bitte geben Sie mir mindestens:**
- 1-2 konkrete Test-Szenarien (Beispiele 1-3)
- Antworten auf die Fragen zu Familienzulagen/BVG/Privatanteilen
- Prioritätenliste (was ist am wichtigsten)

**Optional aber hilfreich:**
- Vergleichswerte aus Abacus/Sage
- Edge-Cases die bei Ihnen auftreten
- Beispiel-Daten

---

**Ich kann auch sofort starten mit:**
- Integrationstests basierend auf dem aktuellen Code-Verständnis
- Geschäftslogik-Dokumentation basierend auf dem Code
- Sie können dann korrigieren/ergänzen

**Was bevorzugen Sie?**
