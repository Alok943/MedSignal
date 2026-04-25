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
# Critical flags that must never be downgraded
# -----------------------------
ALWAYS_CRITICAL = {
    "Probable ACS", "Possible Stroke", "Sepsis Risk", "Hypotension",
    "Meningitis Triad", "Adrenal Crisis", "Serotonin Syndrome Risk",
    "Diabetic Ketoacidosis", "Anaphylaxis", "Organophosphate Poisoning",
    "Heat Stroke", "Pregnancy Bleeding Risk", "Ectopic Pregnancy Risk",
    "Pulmonary Embolism Risk", "Pre-eclampsia Risk", "Acute Liver Failure",
    "Snake Envenomation", "Upper GI Bleed","Rabies Exposure Risk", "Tetanus Prone Wound", 
    "Head Injury Red Flag",
    "Compartment Syndrome", "Major Burn", "Scorpion Envenomation",
    "Occult Fracture Risk"
}

# -----------------------------
# Risk Patterns (Global + India)
# -----------------------------
RISK_PATTERNS = [

    {
    "name": "Rabies Exposure Risk",
    "severity": "CRITICAL",
    "exposure_any": ["dog bite", "cat bite", "monkey bite", "animal bite", "bat bite", "stray bite"],
    "symptoms_any": ["bite wound", "scratch", "bleeding", "puncture"],
    "weights": {"exposure": 3, "symptom": 2},
    "min_required_weight": 3,
    "reasoning": "Mammalian bite — rabies PEP urgently needed",
},

{
    "name": "Tetanus Prone Wound",
    "severity": "CRITICAL",
    "exposure_any": ["puncture wound", "rusty nail", "dirty wound", "road traffic accident", "laceration", "farm injury", "old wound"],
    "conditions_any": ["unvaccinated", "no tetanus", "unknown vaccine"],
    "weights": {"exposure": 3, "condition": 2},
    "min_required_weight": 3,
    "reasoning": "Dirty/tetanus-prone wound without immunization",
},

{
    "name": "Head Injury Red Flag",
    "severity": "CRITICAL",
    "exposure_any": ["head trauma", "head injury", "fall on head", "road traffic accident", "assault"],
    "symptoms_any": ["vomiting", "loss of consciousness", "confusion", "drowsy", "seizure", "headache worsening", "bleeding ear", "bleeding nose"],
    "meds_any": ["warfarin", "apixaban", "rivaroxaban", "clopidogrel", "aspirin"],
    "weights": {"exposure": 2, "symptom": 2, "med": 2},
    "min_required_weight": 4,
    "reasoning": "Head trauma + red flag symptom or anticoagulant",
},

{
    "name": "Compartment Syndrome",
    "severity": "CRITICAL",
    "exposure_any": ["fracture", "crush injury", "tight cast", "old accident"],
    "symptoms_any": ["severe pain", "pain out of proportion", "numbness", "tingling", "pale", "cold limb", "cannot move fingers", "cannot move toes"],
    "weights": {"exposure": 2, "symptom": 3},
    "min_required_weight": 4,
    "reasoning": "Trauma + pain/paresthesia/pallor — limb ischemia risk",
},

{
    "name": "Occult Fracture Risk",
    "severity": "HIGH",
    "exposure_any": ["old accident", "fall", "twist", "trauma last week", "hairline"],
    "symptoms_any": ["persistent pain", "localized tenderness", "swelling", "cannot bear weight", "limp"],
    "weights": {"exposure": 2, "symptom": 2},
    "min_required_weight": 3,
    "reasoning": "History of trauma + ongoing localized pain — X-ray needed",
},

{
    "name": "Major Burn",
    "severity": "CRITICAL",
    "exposure_any": ["burn", "scald", "flame", "electrical burn", "chemical burn"],
    "symptoms_any": ["face burn", "hand burn", "genital burn", "circumferential", "blistering", "difficulty breathing", "hoarse voice"],
    "weights": {"exposure": 2, "symptom": 3},
    "min_required_weight": 4,
    "reasoning": "Burn involving airway, face/hands, or large area",
},

{
    "name": "Scorpion Envenomation",
    "severity": "CRITICAL",
    "exposure_any": ["scorpion sting", "scorpion bite"],
    "symptoms_any": ["sweating", "vomiting", "restlessness", "cold extremities", "breathlessness", "priapism", "hypertension"],
    "weights": {"exposure": 3, "symptom": 2},
    "min_required_weight": 3,
    "reasoning": "Scorpion sting + autonomic symptoms — common in rural India",
},
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
        "min_required_weight": 5,  # FIX: was 4, now requires 1 risk factor
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
    "severity": "MEDIUM",
    "conditions_any": ["diabetes"],
    "symptoms_any": ["confusion", "loss of consciousness", "seizure"],
    "meds_any": ["insulin", "glimepiride", "gliclazide"],
    "weights": {"symptom": 3, "med": 2},
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
    "weights": {"symptom": 3, "exposure": 3},
    "min_required_weight": 4,
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
        "context_month": [6, 7, 8, 9, 10],
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
        "min_required_weight": 5,  # FIX: was 3, now requires BP + symptom
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
        "min_required_weight": 5,  # FIX: was 3, now requires exposure
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
        "min_required_weight": 5,  # FIX: was 3, now requires symptom
        "reasoning": "Pregnant + bleeding or pain",
    },

    {
        "name": "Ectopic Pregnancy Risk",
        "severity": "CRITICAL",
        "conditions_any": ["pregnant", "pregnancy"],
        "symptoms_any": ["abdominal pain", "right side pain", "one sided pain", "spotting", "vaginal bleeding", "shoulder pain", "dizziness", "syncope"],
        "weights": {"condition": 3, "symptom": 3},
        "min_required_weight": 6,
        "reasoning": "Pregnancy + unilateral pain/bleeding — ectopic until proven otherwise",
    },

    {
        "name": "Pulmonary Embolism Risk",
        "severity": "CRITICAL",
        "symptoms_any": ["breathlessness", "shortness of breath", "chest pain", "cough blood"],
        "vitals_any": ["tachycardia", "fast heart rate", "low oxygen", "hypoxia"],
        "signs_any": ["leg swelling", "calf pain", "unilateral swelling"],
        "weights": {"symptom": 2, "vital": 2, "sign": 2},
        "min_required_weight": 4,
        "reasoning": "Breathlessness + tachycardia/leg swelling",
    },

    {
        "name": "Pre-eclampsia Risk",
        "severity": "CRITICAL",
        "conditions_any": ["pregnant", "pregnancy"],
        "vitals_any": ["bp >140/90", "high bp", "hypertension"],
        "symptoms_any": ["headache", "visual disturbance", "blurred vision", "swelling", "epigastric pain"],
        "weights": {"condition": 2, "vital": 2, "symptom": 2},
        "min_required_weight": 4,
        "reasoning": "Pregnancy + hypertension + end-organ symptom",
    },

    {
        "name": "Acute Liver Failure",
        "severity": "CRITICAL",
        "symptoms_any": ["jaundice", "yellow eyes", "confusion", "drowsy", "bleeding"],
        "conditions_any": ["hepatitis", "liver disease"],
        "habits_any": ["alcohol"],
        "weights": {"symptom": 3, "condition": 1, "habit": 1},
        "min_required_weight": 4,
        "reasoning": "Jaundice + encephalopathy/coagulopathy",
    },

    {
        "name": "Snake Envenomation",
        "severity": "CRITICAL",
        "exposure_any": ["snake bite", "snakebite", "unknown bite"],
        "symptoms_any": ["ptosis", "difficulty breathing", "bleeding gums", "swelling", "pain"],
        "weights": {"exposure": 3, "symptom": 2},
        "min_required_weight": 3,
        "reasoning": "Snake exposure + neurotoxic/hemotoxic signs",
    },

    {
        "name": "Upper GI Bleed",
        "severity": "CRITICAL",
        "symptoms_any": ["vomiting blood", "hematemesis", "black stools", "melena"],
        "vitals_any": ["hypotension", "low bp", "tachycardia"],
        "weights": {"symptom": 3, "vital": 2},
        "min_required_weight": 3,
        "reasoning": "Hematemesis/melena + hemodynamic instability",
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
        "habits_any": ["heavy alcohol", "binge drinking", "alcohol", "drink heavily", "drinks heavily", "units/day", "units per day"],
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
    if "exposure_any" in pattern and match_any(symptoms + habits + conditions, pattern["exposure_any"]):
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
            if r.flag not in ALWAYS_CRITICAL:
                if r.severity == "CRITICAL":
                    r.severity = "HIGH"

    # ==============================
    # 🔧 FINAL SAFETY GUARD
    # Prevent accidental CRITICAL escalation
    # ==============================
    if not any(r.flag in ALWAYS_CRITICAL for r in results):
        for r in results:
            if r.severity == "CRITICAL":
                r.severity = "HIGH"

    return results