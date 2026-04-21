import requests, re
from dataclasses import dataclass
from typing import List, Optional

OPENFDA_BASE = "https://api.fda.gov/drug/label.json"
_session = requests.Session()
_cache = {}

ALIASES = {"paracetamol": "acetaminophen", "crocin": "acetaminophen", "disprin": "aspirin"}
STOPWORDS = {"tablet", "capsule", "syrup", "vitamin", "supplement", "injection", "drops", "tonic"}

@dataclass
class DrugInteractionResult:
    drug_pair: str
    interaction_found: bool
    warning_text: Optional[str]
    source: str # openfda / not_found / error / timeout / rate_limited

def _clean(drug: str) -> str:
    d = drug.lower().strip()
    d = re.sub(r'\d+\.?\d*\s*(mg|mcg|g|ml|iu)', '', d).strip()
    d = ALIASES.get(d, d)
    return "" if d in STOPWORDS else d

def query_drug_interactions(drug1: str, drug2: str) -> DrugInteractionResult:
    d1, d2 = _clean(drug1), _clean(drug2)
    if not d1 or not d2 or d1 == d2: # fix #1 and #2
        return DrugInteractionResult(f"{d1}+{d2}", False, None, "not_found")

    key = tuple(sorted([d1, d2]))
    if key in _cache:
        return _cache[key]

    try:
        params = {"search": f'openfda.generic_name:"{d1}"', "limit": 5}
        resp = _session.get(OPENFDA_BASE, params=params, timeout=4)

        if resp.status_code!= 200: # fix #6
            result = DrugInteractionResult(f"{d1} + {d2}", False,
                "OpenFDA unavailable" if resp.status_code!= 429 else "Rate limited",
                "error" if resp.status_code!= 429 else "rate_limited")
            _cache[key] = result
            return result

        for item in resp.json().get("results", []):
            full_text = " ".join([*item.get("warnings", []), *item.get("drug_interactions", []),
                                  *item.get("boxed_warning", []), *item.get("precautions", [])])
            text_lower = full_text.lower()

            tokens = list(set( d1.split()+ d2.split())) # fix #5
            if any(re.search(rf'\b{re.escape(t)}\b', text_lower) for t in tokens):
                # extract sentence, keep original case
                sentence = next((s for s in re.split(r'[.;]', full_text)
                                if any(t in s.lower() for t in tokens)), full_text[:200])
                warning = sentence.strip()[:200] # fix #3

                result = DrugInteractionResult(f"{d1} + {d2}", True, warning, "openfda")
                _cache[key] = result
                return result

        result = DrugInteractionResult(f"{d1} + {d2}", False, None, "not_found")

    except requests.exceptions.Timeout:
        result = DrugInteractionResult(f"{d1} + {d2}", False, "OpenFDA timeout", "timeout")
    except Exception as e:
        result = DrugInteractionResult(f"{d1} + {d2}", False, str(e)[:100], "error")

    _cache[key] = result
    return result

def check_all_interactions(medications: List[str], max_pairs: int = 10) -> List[DrugInteractionResult]:
    meds = [m for m in {_clean(m) for m in medications if m} if m] # fix #1
    if len(meds) < 2:
        return []

    results, count = [], 0
    for i in range(len(meds)):
        for j in range(i+1, len(meds)):
            if count >= max_pairs:
                break
            res = query_drug_interactions(meds[i], meds[j])
            if res.interaction_found:
                results.append(res)
            count += 1

    results.sort(key=lambda x: x.interaction_found, reverse=True) # fix #7
    return results