from dataclasses import dataclass

@dataclass
class RuleMatch:
    severity: str  # CRITICAL, HIGH, MEDIUM
    flag: str
    reasoning: str

def run_hard_rules(structured_input: dict) -> list[RuleMatch]:
    flags = []
    
    symptoms = [s.lower() for s in structured_input.get("symptoms", [])]
    medications = [m.lower() for m in structured_input.get("medications", [])]
    habits = [h.lower() for h in structured_input.get("habits", [])]
    age = structured_input.get("age", 0)
    conditions = [c.lower() for c in structured_input.get("conditions", [])]

    # Rule 1 — ACS
    if ("chest pain" in symptoms or "chest tightness" in symptoms):
        if any(c in conditions for c in ["diabetes", "diabetic"]):
            if age > 50:
                flags.append(RuleMatch("CRITICAL", "Probable ACS", "Chest pain + diabetes + age > 50"))

    # Rule 2 — Serotonin Syndrome
    if any("maoi" in m for m in medications):
        serotonergic = ["ssri", "snri", "tramadol", "fentanyl", "lithium"]
        if any(any(s in m for s in serotonergic) for m in medications):
            flags.append(RuleMatch("CRITICAL", "Serotonin Syndrome Risk", "MAOI + serotonergic agent"))

    # Rule 3 — Warfarin + CYP interaction
    if any("warfarin" in m for m in medications):
        interactors = ["clarithromycin", "fluconazole", "metronidazole"]
        for drug in interactors:
            if any(drug in m for m in medications):
                flags.append(RuleMatch("HIGH", "Bleeding Risk", f"Warfarin + {drug}"))

    # Rule 4 — Paracetamol + Alcohol
    if any("paracetamol" in m or "acetaminophen" in m for m in medications):
        if any("alcohol" in h for h in habits):
            flags.append(RuleMatch("HIGH", "Hepatotoxicity Risk", "Paracetamol + heavy alcohol use"))

    # Rule 5 — Meningitis triad
    if all(s in symptoms for s in ["fever", "confusion", "neck stiffness"]):
        flags.append(RuleMatch("CRITICAL", "Possible Meningitis", "Fever + confusion + neck stiffness"))

    # Rule 6 — Adrenal Crisis
    if any("corticosteroid" in m or "steroid" in m for m in medications):
        if "fever" in symptoms and ("hypotension" in symptoms or "low bp" in symptoms):
            flags.append(RuleMatch("CRITICAL", "Adrenal Crisis Risk", "Corticosteroid use + fever + hypotension"))

    # Rule 7 — Opioid + Benzo
    if any("opioid" in m or "morphine" in m or "oxycodone" in m or "fentanyl" in m for m in medications):
        if any("benzodiazepine" in m or "diazepam" in m or "alprazolam" in m for m in medications):
            flags.append(RuleMatch("HIGH", "Respiratory Depression Risk", "Opioid + benzodiazepine combination"))

    return flags