from typing import List, Dict, Any
from src.models.candidate import Candidate

SOURCE_PRIORITY = ["recruiter_csv", "linkedin", "github", "resume", "recruiter_notes"]

MERGE_POLICY = {
    "full_name": "priority",       # CSV -> GitHub
    "headline": "priority",        # prefer recruiter, else GitHub bio
    "years_experience": "priority",
    "emails": "union",
    "phones": "union",
    "skills_raw": "union",
}


def merge(records: List[Dict[str, Any]], candidate_id: str) -> Candidate:
    """
    Input: list of NORMALIZED raw records (already cleaned by normalizer.py).
    Output: one canonical Candidate dataclass with provenance recorded per field.
    """
    candidate = Candidate(candidate_id=candidate_id)
    ordered = _sorted_by_priority(records)

    # Priority-pick scalars
    for field_name in ["full_name", "headline", "years_experience"]:
        value, source = _pick_first_nonnull(ordered, field_name)
        setattr(candidate, field_name, value)
        if source:
            candidate.provenance[field_name] = {
                "field": field_name, "value": value, "source": source, "method": "priority_pick"
            }

    # Union: emails
    emails, sources = _union(records, "emails")
    candidate.emails = emails
    if emails:
        candidate.provenance["emails"] = {
            "field": "emails", "value": emails, "source": sources, "method": "union_deduplicated"
        }

    # Union: phones
    phones, sources = _union(records, "phones")
    candidate.phones = phones
    if phones:
        candidate.provenance["phones"] = {
            "field": "phones", "value": phones, "source": sources, "method": "union_deduplicated"
        }

    # Location: first non-null in priority order
    for rec in ordered:
        if rec.get("location"):
            candidate.location = rec["location"]
            candidate.provenance["location"] = {
                "field": "location", "value": rec["location"], "source": rec.get("_source"), "method": "priority_pick"
            }
            break

    # Links: merge by type, first source to populate a key wins that key
    link_sources = {}
    for rec in records:
        links = rec.get("links", {}) or {}
        for key in ["linkedin", "github", "portfolio"]:
            if links.get(key) and not candidate.links.get(key):
                candidate.links[key] = links[key]
                link_sources[key] = rec.get("_source")
        for other in links.get("other", []):
            if other not in candidate.links["other"]:
                candidate.links["other"].append(other)
    if link_sources:
        candidate.provenance["links"] = {
            "field": "links", "value": candidate.links, "source": link_sources, "method": "merge_by_type"
        }

    # Skills: union, confidence weighted by how many sources agree
    skills_map: Dict[str, Dict[str, Any]] = {}
    for rec in records:
        source = rec.get("_source", "unknown")
        base_confidence = 0.75 if source == "recruiter_csv" else 0.55
        for skill in rec.get("skills_raw", []):
            if skill in skills_map:
                if source not in skills_map[skill]["sources"]:
                    skills_map[skill]["sources"].append(source)
                    skills_map[skill]["confidence"] = min(1.0, skills_map[skill]["confidence"] + 0.15)
            else:
                skills_map[skill] = {"name": skill, "confidence": base_confidence, "sources": [source]}
    candidate.skills = list(skills_map.values())
    if candidate.skills:
        candidate.provenance["skills"] = {
            "field": "skills", "value": [s["name"] for s in candidate.skills],
            "source": list({s for skill in candidate.skills for s in skill["sources"]}),
            "method": "union_weighted"
        }

    return candidate


def _pick_first_nonnull(ordered_records, field_name):
    for rec in ordered_records:
        val = rec.get(field_name)
        if val not in (None, ""):
            return val, rec.get("_source", "unknown")
    return None, None


def _union(records, field_name):
    seen, out, sources = set(), [], []
    for rec in records:
        for val in rec.get(field_name, []):
            if val not in seen:
                seen.add(val)
                out.append(val)
                sources.append(rec.get("_source", "unknown"))
    return out, list(set(sources))


def _sorted_by_priority(records):
    def priority(rec):
        src = rec.get("_source", "unknown")
        return SOURCE_PRIORITY.index(src) if src in SOURCE_PRIORITY else 99
    return sorted(records, key=priority)