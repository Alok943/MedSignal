# test just the cleaning pipeline
from agents.intake_agent import clean_intake, compute_data_quality, compute_missing_fields
import json

mappings = json.load(open("data/mappings.json"))

mock = {
    "age": 65, "sex": "male",
    "symptoms": ["chest dabav", "saans phoolna"],
    "vitals": [], "conditions": ["sugar"],
    "medications": [], "habits": ["smoking"],
    "history": [], "timeline": {"onset": "achanak", "duration": None},
    "negations": [], "uncertain": [],
    "missing_fields": [], "data_quality": "LOW",
    "original_text": "65 male, chest dabav, saans phoolna, sugar patient, achanak shuru hua"
}

result = clean_intake(mock, mappings)
result["missing_fields"] = compute_missing_fields(result)
result["data_quality"] = compute_data_quality(result)
print(result)