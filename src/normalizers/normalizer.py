import re
from typing import Optional, Dict, Any, List

SKILL_ALIASES = {
    "js": "JavaScript", "javascript": "JavaScript",
    "ts": "TypeScript", "typescript": "TypeScript",
    "py": "Python", "python": "Python",
    "ml": "Machine Learning",
    "golang": "Go", "go": "Go",
    "c++": "C++", "cpp": "C++",
    "c#": "C#", "csharp": "C#",
    "html": "HTML", "css": "CSS",
}

COUNTRY_TO_CODE = {
    "india": "IN", "united states": "US", "usa": "US", "u.s.a.": "US",
    "united kingdom": "GB", "uk": "GB", "canada": "CA", "germany": "DE",
    "france": "FR", "australia": "AU", "singapore": "SG",
}


def normalize_email(email: str) -> Optional[str]:
    if not email:
        return None
    email = email.strip().lower()
    pattern = r'^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$'
    return email if re.match(pattern, email) else None


def normalize_phone(phone: str) -> Optional[str]:
    if not phone:
        return None
    digits = re.sub(r'\D', '', phone)
    if len(digits) == 10:
        return f"+91{digits}"
    elif len(digits) == 12 and digits.startswith("91"):
        return f"+{digits}"
    elif 7 < len(digits) <= 15:
        return f"+{digits}"
    return None  # implausible length — don't fabricate


def normalize_url(url: str) -> Optional[str]:
    if not url:
        return None
    url = url.strip()
    if not url:
        return None
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    return url.rstrip("/")


def normalize_skill(skill: str) -> str:
    if not skill:
        return skill
    return SKILL_ALIASES.get(skill.lower().strip(), skill.strip())


def normalize_country(country: str) -> Dict[str, Optional[str]]:
    if not country:
        return {"country": None, "country_code": None}
    clean = country.strip()
    code = COUNTRY_TO_CODE.get(clean.lower())
    return {"country": clean, "country_code": code}


def normalize_location(raw: str) -> Optional[Dict[str, Optional[str]]]:
    if not raw:
        return None

    parts = [p.strip() for p in raw.split(",") if p.strip()]
    if not parts:
        return None

    result = {
        "city": None,
        "region": None,
        "country": None,
        "country_code": None,
    }

    if len(parts) == 1:
        country_info = normalize_country(parts[0])

        if country_info["country_code"]:
            result.update(country_info)
        else:
            result["city"] = parts[0]

    elif len(parts) == 2:
        result["city"], result["region"] = parts[0], parts[1]

    else:
        result["city"], result["region"] = parts[0], parts[1]
        country_info = normalize_country(parts[2])
        result.update(country_info)

    return result


def dedupe(values: List[str]) -> List[str]:
    seen, out = set(), []
    for v in values:
        if v and v not in seen:
            seen.add(v)
            out.append(v)
    return out


def normalize_record(record: Dict[str, Any]) -> Dict[str, Any]:
    """
    Pipeline stage: takes one raw parser record, returns a normalized record
    of the same shape. Does NOT merge across sources, does NOT score confidence.
    """
    normalized = dict(record)  # shallow copy, preserve _source/_raw/_meta

    normalized["emails"] = dedupe(
        [e for e in (normalize_email(x) for x in record.get("emails", [])) if e]
    )

    normalized["phones"] = dedupe(
        [p for p in (normalize_phone(x) for x in record.get("phones", [])) if p]
    )

    full_name = record.get("full_name")
    normalized["full_name"] = (
        full_name.strip()
        if isinstance(full_name, str) and full_name.strip()
        else None
    )

    headline = record.get("headline")
    normalized["headline"] = (
        " ".join(headline.split())
        if isinstance(headline, str) and headline.strip()
        else None
    )

    links = record.get("links", {}) or {}
    normalized["links"] = {
        "linkedin": normalize_url(links.get("linkedin")),
        "github": normalize_url(links.get("github")),
        "portfolio": normalize_url(links.get("portfolio")),
        "other": dedupe([normalize_url(u) for u in links.get("other", [])]),
    }

    loc_raw = record.get("location_raw")
    normalized["location"] = normalize_location(loc_raw) if loc_raw else None

    years = record.get("years_experience")
    try:
        normalized["years_experience"] = (
            float(years) if years not in (None, "") else None
        )
    except (ValueError, TypeError):
        normalized["years_experience"] = None

    normalized["skills_raw"] = dedupe(
        [normalize_skill(s) for s in record.get("skills_raw", [])]
    )

    return normalized