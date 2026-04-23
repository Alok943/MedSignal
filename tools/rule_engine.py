from dataclasses import dataclass
from typing import List, Dict, Any


# -----------------------------
# Output Structure
# -----------------------------
@dataclass
class RuleMatch:
    severity: str
    flag: str
    reasoning: str
    confidence: float
    signals: Dict[str, bool]


# -----------------------------
# Risk Patterns (Global + India)
# -----------------------------
RISK_PATTERNS = [

    # -------------------------
    # MENINGITIS (2-of-3 triad)
    # -------------------------
    {
        "name": "Meningitis Triad",
        "severity": "CRITICAL",
        "symptoms_any": ["neck stiffness", "nuchal rigidity", "stiff neck"],
        "warning_any": ["fever", "febrile", "high temperature","light sensitivity", "photophobia"],
        "altered_mental": True,
        "weights": {"symptom": 3, "warning": 3, "mental": 3},
        # 🔧 FIX: Increased threshold to prevent fever-only false positives
        # Requires combination (fever + neck stiffness / mental change)
        "min_required_weight": 6,
        "reasoning": "Meningitis triad: neck stiffness + fever/confusion",
    },

    # -------------------------
    # ADRENAL CRISIS
    # -------------------------
    {
        "name": "Adrenal Crisis",
        "severity": "CRITICAL",
        "meds_any": ["prednisolone", "prednisone", "dexamethasone", "hydrocortisone",
                     "methylprednisolone", "corticosteroid", "steroid"],
        "symptoms_any": ["fever", "hypotension", "low blood pressure", "low bp", "collapse"],
        "altered_mental": True,
        "weights": {"med": 3, "symptom": 2, "mental": 2},
        "min_required_weight": 5,
        "reasoning": "Corticosteroid use + fever + hypotension/confusion",
    },

    # -------------------------
    # SEROTONIN SYNDROME
    # -------------------------
    {
        "name": "Serotonin Syndrome Risk",
        "severity": "CRITICAL",
        "meds_any": ["phenelzine", "tranylcypromine", "selegiline", "moclobemide", "maoi"],
        "meds_co": ["ssri", "sertraline", "fluoxetine", "citalopram", "escitalopram",
                    "paroxetine", "venlafaxine", "duloxetine", "tramadol", "linezolid"],
        "weights": {"med": 3},
        "min_required_weight": 3,
        "reasoning": "MAOI + serotonergic drug combination",
    },
    
    # -------------------------
    # CARDIAC
    # -------------------------
    {
        "name": "Probable ACS",
        "severity": "CRITICAL",
        "symptoms_any": ["chest pain", "chest tightness", "pressure in chest"],
        "conditions_any": ["diabetes", "diabetic"],
        "habits_any": ["smoking", "smoker"],
        "age_min": 50,
        "weights": {"symptom": 4, "condition": 1, "habit": 1, "age": 1},
        "min_required_weight": 4,
        "reasoning": "Chest symptoms + cardiac risk factors",
    },

    # -------------------------
    # NEURO
    # -------------------------
    {
        "name": "Possible Stroke",
        "severity": "CRITICAL",
        "symptoms_any": ["facial droop", "face deviation", "arm weakness", "slurred speech", "sudden weakness"],
        "onset": "sudden",
        "weights": {"symptom": 3, "onset": 2},
        "min_required_weight": 3,
        "reasoning": "FAST criteria",
    },

    # -------------------------
    # SEPSIS
    # -------------------------
    {
        "name": "Sepsis Risk",
        "severity": "CRITICAL",
        "symptoms_any": ["fever", "high fever"],
        "vitals_any": ["hypotension", "low bp", "tachycardia", "fast heart rate"],
        "altered_mental": True,
        "weights": {"symptom": 2, "vital": 2, "mental": 2},
        "min_required_weight": 4,
        "reasoning": "Infection + organ dysfunction",
    },

    # -------------------------
    # ENDOCRINE
    # -------------------------
    {
        "name": "Diabetic Ketoacidosis",
        "severity": "CRITICAL",
        "conditions_any": ["diabetes", "diabetic"],
        "symptoms_any": ["vomiting", "abdominal pain", "deep breathing", "kussmaul", "fruity breath"],
        "weights": {"condition": 2, "symptom": 2},
        "min_required_weight": 3,
        "reasoning": "Known diabetic + metabolic symptoms",
    },

    {
    "name": "Hypoglycemia",
    "severity": "MEDIUM",  # 🔧 downgraded
    "conditions_any": ["diabetes"],
    "symptoms_any": ["confusion", "loss of consciousness", "seizure"],  # 🔧 stricter
    "meds_any": ["insulin", "glimepiride", "gliclazide"],
    "weights": {"symptom": 3, "med": 2},
    # 🔧 FIX: Prevent false positives (confusion alone shouldn't trigger hypoglycemia)
    # Requires BOTH medication exposure + neuro symptoms
    "min_required_weight": 5,
    "reasoning": "Diabetic on meds + neuroglycopenic symptoms",
    },

    # -------------------------
    # ALLERGY
    # -------------------------
    {
    "name": "Anaphylaxis",
    "severity": "CRITICAL",
    "symptoms_any": ["wheeze", "swelling face", "lip swelling", "hives"],
    "exposure_any": ["new drug", "injection", "food", "insect bite"],
    "weights": {"symptom": 3, "exposure": 3},  # 🔧 stronger requirement
    "min_required_weight": 4,  # 🔧 requires BOTH
    "reasoning": "Allergic reaction with airway involvement",
    },

    # -------------------------
    # VECTOR (India)
    # -------------------------
    {
        "name": "Dengue Warning Signs",
        "severity": "HIGH",
        "symptoms_any": ["fever", "high fever"],
        "warning_any": ["abdominal pain", "persistent vomiting", "bleeding gums", "nose bleed", "lethargy", "restlessness"],
        "context_month": [6, 7, 8, 9, 10],  # optional
        "weights": {"symptom": 2, "warning": 3, "season": 1},
        "min_required_weight": 4,
        "reasoning": "Fever + warning sign in monsoon",
    },

    # -------------------------
    # TB
    # -------------------------
    {
        "name": "Pulmonary TB Red Flag",
        "severity": "HIGH",
        "symptoms_any": ["chronic cough", "cough >2 weeks", "hemoptysis", "blood in sputum", "weight loss", "night sweats"],
        "weights": {"symptom": 2},
        "min_required_weight": 2,
        "reasoning": "Prolonged cough with systemic signs",
    },

    # -------------------------
    # HYPERTENSION
    # -------------------------
    {
        "name": "Hypertensive Emergency",
        "severity": "CRITICAL",
        "vitals_any": ["bp >180/120", "very high bp"],
        "symptoms_any": ["chest pain", "breathlessness", "confusion", "headache", "visual disturbance"],
        "weights": {"vital": 3, "symptom": 2},
        "min_required_weight": 3,
        "reasoning": "Severe BP + end-organ symptom",
    },

    # -------------------------
    # PEDIATRIC
    # -------------------------
    {
        "name": "Severe Dehydration",
        "severity": "HIGH",
        "symptoms_any": ["diarrhea", "vomiting", "loose motions"],
        "signs_any": ["lethargy", "sunken eyes", "reduced urine"],
        "age_max": 5,
        "weights": {"symptom": 2, "sign": 2},
        "min_required_weight": 3,
        "reasoning": "GI losses + dehydration signs",
    },

    # -------------------------
    # TOXICOLOGY
    # -------------------------
    {
        "name": "Organophosphate Poisoning",
        "severity": "CRITICAL",
        "exposure_any": ["pesticide", "insecticide", "organophosphate", "spray"],
        "symptoms_any": ["excessive salivation", "pinpoint pupils", "breathlessness"],
        "weights": {"exposure": 3, "symptom": 2},
        "min_required_weight": 4,
        "reasoning": "Exposure + cholinergic toxidrome",
    },

    # -------------------------
    # ENVIRONMENT
    # -------------------------
    {
        "name": "Heat Stroke",
        "severity": "CRITICAL",
        "symptoms_any": ["high fever", "confusion", "hot dry skin", "collapse"],
        "exposure_any": ["heat exposure", "outdoor work"],
        "weights": {"symptom": 3, "exposure": 2},
        "min_required_weight": 3,
        "reasoning": "Heat exposure + CNS dysfunction",
    },

    # -------------------------
    # OBSTETRIC
    # -------------------------
    {
        "name": "Pregnancy Bleeding Risk",
        "severity": "CRITICAL",
        "conditions_any": ["pregnant", "pregnancy"],
        "symptoms_any": ["vaginal bleeding", "abdominal pain", "dizziness"],
        "weights": {"condition": 3, "symptom": 2},
        "min_required_weight": 3,
        "reasoning": "Pregnant + bleeding or pain",
    },

    # -------------------------
    # DRUG INTERACTIONS
    # -------------------------
    {
        "name": "Bleeding Risk",
        "severity": "HIGH",
        "meds_any": ["warfarin"],
        "meds_co": ["clarithromycin", "fluconazole", "metronidazole"],
        "weights": {"med": 3},
        "min_required_weight": 3,
        "reasoning": "Warfarin + interacting drug",
    },
    {
        "name": "Hepatotoxicity Risk",
        "severity": "HIGH",
        "meds_any": ["paracetamol", "acetaminophen"],
        "habits_any": ["heavy alcohol", "binge drinking"],
        "weights": {"med": 2, "habit": 2},
        "min_required_weight": 3,
        "reasoning": "Paracetamol + alcohol",
    },
    {
        "name": "Respiratory Depression Risk",
        "severity": "HIGH",
        "meds_any": ["opioid", "morphine", "fentanyl", "oxycodone"],
        "meds_co": ["benzodiazepine", "diazepam", "alprazolam"],
        "weights": {"med": 3},
        "min_required_weight": 3,
        "reasoning": "Opioid + benzodiazepine",
    },
    ]


# -----------------------------
# Helpers
# -----------------------------
def normalize_list(items):
    return [str(i).lower().strip() for i in items if i]


def match_any(text_list, keywords):
    return any(any(k in t for k in keywords) for t in text_list)


def match_all(text_list, keywords):
    return all(any(k in t for t in text_list) for k in keywords)


# -----------------------------
# Evaluator
# -----------------------------
def evaluate_pattern(pattern: Dict[str, Any], data: Dict[str, Any]):

    symptoms = data["symptoms"]
    medications = data["medications"]
    habits = data["habits"]
    conditions = data["conditions"]
    vitals = data.get("vitals", [])
    age = data["age"]
    month = data.get("month")

    matched_weight = 0
    total_weight = sum(pattern.get("weights", {}).values())
    signals = {}

    # symptoms
    if "symptoms_any" in pattern and match_any(symptoms, pattern["symptoms_any"]):
        matched_weight += pattern["weights"].get("symptom", 0)
        signals["symptom"] = True

    # conditions
    if "conditions_any" in pattern and match_any(conditions, pattern["conditions_any"]):
        matched_weight += pattern["weights"].get("condition", 0)
        signals["condition"] = True

    # habits
    if "habits_any" in pattern and match_any(habits, pattern["habits_any"]):
        matched_weight += pattern["weights"].get("habit", 0)
        signals["habit"] = True

    # meds
    if "meds_any" in pattern and match_any(medications, pattern["meds_any"]):
        matched_weight += pattern["weights"].get("med", 0)
        signals["med"] = True
    
    # co-medication (any of meds_any AND any of meds_co both present)
    if "meds_co" in pattern:
        if signals.get("med") and match_any(medications, pattern["meds_co"]):
            signals["med_co"] = True
        

    if "meds_all" in pattern and match_all(medications, pattern["meds_all"]):
        matched_weight += pattern["weights"].get("med", 0)
        signals["med"] = True

    # vitals (separate field)
    if "vitals_any" in pattern and match_any(vitals, pattern["vitals_any"]):
        matched_weight += pattern["weights"].get("vital", 0)
        signals["vital"] = True

    # signs / warnings
    if "signs_any" in pattern and match_any(symptoms, pattern["signs_any"]):
        matched_weight += pattern["weights"].get("sign", 0)
        signals["sign"] = True

    if "warning_any" in pattern and match_any(symptoms, pattern["warning_any"]):
        matched_weight += pattern["weights"].get("warning", 0)
        signals["warning"] = True

    # exposure
    if "exposure_any" in pattern and match_any(symptoms + habits, pattern["exposure_any"]):
        matched_weight += pattern["weights"].get("exposure", 0)
        signals["exposure"] = True

    # age
    if "age_min" in pattern and age and age >= pattern["age_min"]:
        matched_weight += pattern["weights"].get("age", 0)
        signals["age"] = True

    if "age_max" in pattern and age and age <= pattern["age_max"]:
        matched_weight += pattern["weights"].get("age", 0)
        signals["age"] = True

    # altered mental
    if pattern.get("altered_mental"):
        if match_any(symptoms, ["confusion", "drowsy", "altered"]):
            matched_weight += pattern["weights"].get("mental", 0)
            signals["mental"] = True

    # onset
    if pattern.get("onset") == "sudden":
        if match_any(symptoms, ["sudden", "suddenly"]):
            matched_weight += pattern["weights"].get("onset", 0)
            signals["onset"] = True

    # seasonal (optional)
    # if month not provided → skipped intentionally (no penalty)
    if "context_month" in pattern and month:
        if month in pattern["context_month"]:
            matched_weight += pattern["weights"].get("season", 0)
            signals["season"] = True

    if "meds_co" in pattern and not signals.get("med_co"):
        matched_weight -= pattern["weights"].get("med", 0)
        signals.pop("med", None)
    
    # ==============================
    # 🔧 CLINICAL SAFETY GUARDS
    # ==============================

    # 🔧 FIX: Prevent meningitis false positive (requires neck stiffness)
    if pattern["name"] == "Meningitis Triad":
        if not match_any(symptoms, ["neck stiffness", "stiff neck", "nuchal rigidity"]):
            return None

    # 🔧 FIX: Hypoglycemia must have diabetes or medication context
    if pattern["name"] == "Hypoglycemia":
        if not (
            match_any(conditions, ["diabetes"]) or
            match_any(medications, ["insulin", "glimepiride", "gliclazide"])
    ):
            return None

    # 🔧 FIX: Dengue must have fever (avoid seasonal + abdominal pain false positives)
    if pattern["name"] == "Dengue Warning Signs":
        if not match_any(symptoms, ["fever", "high fever"]):
            return None
    # 🔧 FIX: Anaphylaxis requires BOTH exposure + airway symptom
    if pattern["name"] == "Anaphylaxis":
        if not signals.get("exposure"):
            return None
    
    # threshold
    if matched_weight < pattern.get("min_required_weight", 1):
        return None

    # confidence
    base_conf = matched_weight / total_weight if total_weight else 0

    missing = 0
    if not medications:
        missing += 1
    if not conditions:
        missing += 1
    if not age:
        missing += 1

    penalty = min(0.3, 0.15 * missing)
    confidence = max(0.3, base_conf - penalty)

    return RuleMatch(
        severity=pattern["severity"],
        flag=pattern["name"],
        reasoning=pattern["reasoning"],
        confidence=round(confidence, 2),
        signals=signals,
    )


# -----------------------------
# Main Function
# -----------------------------
def run_hard_rules(structured_input: Dict) -> List[RuleMatch]:

    data = {
        "symptoms": normalize_list(structured_input.get("symptoms", [])),
        "medications": normalize_list(structured_input.get("medications", [])),
        "habits": normalize_list(structured_input.get("habits", [])),
        "conditions": normalize_list(structured_input.get("conditions", [])),
        "vitals": normalize_list(structured_input.get("vitals", [])),
        "age": structured_input.get("age", 0),
        "month": structured_input.get("month"),
    }

    # ✅ STEP 1: initialize results
    results = []

    # ==============================
    # 🔧 NEW: Numeric vitals parsing
    # Detect hypotension from values like "80/50"
    # ==============================
    for v in data["vitals"]:
        if "/" in v:
            try:
                systolic = int(v.split("/")[0])
                if systolic < 90:
                    results.append(RuleMatch(
                        severity="CRITICAL",
                        flag="Hypotension",
                        reasoning="Systolic BP < 90",
                        confidence=1.0,
                        signals={"vital": True}
                    ))
            except:
                pass

    # ✅ STEP 2: collect matches
    for pattern in RISK_PATTERNS:
        match = evaluate_pattern(pattern, data)
        if match:
            results.append(match)

    # ==============================
    # ✅ STEP 3: POST-PROCESSING (control layer)
    # ==============================

    # 🔧 FIX: Prevent TB false positives without cough
    results = [
        r for r in results
        if not (r.flag == "Pulmonary TB Red Flag" and "cough" not in " ".join(data["symptoms"]))
    ]

    # 🔧 CONTROL: Cardiac emergencies dominate weaker risks
    has_acs = any(r.flag == "Probable ACS" for r in results)

    if has_acs:
        for r in results:
            if r.flag == "Hypoglycemia":
                r.severity = "MEDIUM"

    # 🔧 CONTROL: Avoid too many CRITICAL flags (alarm fatigue)
    critical_count = sum(1 for r in results if r.severity == "CRITICAL")

    if critical_count > 2:
        for r in results:
            if r.flag not in ["Probable ACS", "Possible Stroke", "Sepsis Risk"]:
                if r.severity == "CRITICAL":
                    r.severity = "HIGH"

    # ==============================
    # 🔧 FINAL SAFETY GUARD
    # Prevent accidental CRITICAL escalation
    # ==============================
    if not any(r.flag in ["Probable ACS", "Possible Stroke", "Sepsis Risk", "Hypotension"] for r in results):
        for r in results:
            if r.severity == "CRITICAL":
                r.severity = "HIGH"

    return results