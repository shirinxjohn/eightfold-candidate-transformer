from typing import Tuple, List
from src.models.candidate import Candidate

REQUIRED_FIELDS = ["full_name", "emails"]

FIELD_WEIGHTS = {
    "full_name": 0.20,
    "emails": 0.18,
    "phones": 0.10,
    "location": 0.08,
    "headline": 0.08,
    "years_experience": 0.06,
    "skills": 0.10,
    "links": 0.08,
    "experience": 0.06,
    "education": 0.06,
}


def score(candidate: Candidate) -> Tuple[float, List[str]]:
    """
    Returns (score, reasons). Entirely rule-based:
      - +weight per populated field
      - +bonus if multiple sources agree on a field (from provenance)
      - -penalty per missing required field
    """
    total = 0.0
    reasons = []

    for field_name, weight in FIELD_WEIGHTS.items():
        val = getattr(candidate, field_name, None)
        if _is_populated(val):
            total += weight
            reasons.append(f"+{weight} {field_name} populated")

            prov = candidate.provenance.get(field_name, {})
            sources = prov.get("source")
            if isinstance(sources, list) and len(sources) > 1:
                bonus = 0.03
                total += bonus
                reasons.append(f"+{bonus} {field_name} corroborated by {len(sources)} sources")

    for required in REQUIRED_FIELDS:
        val = getattr(candidate, required, None)
        if not _is_populated(val):
            penalty = 0.15
            total -= penalty
            reasons.append(f"-{penalty} required field '{required}' missing")

    final = round(max(0.0, min(total, 1.0)), 3)
    return final, reasons


def _is_populated(val) -> bool:
    if val is None:
        return False
    if isinstance(val, (list, dict)) and len(val) == 0:
        return False
    if isinstance(val, dict) and all(v in (None, [], {}) for v in val.values()):
        return False
    return True