from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any


@dataclass
class Candidate:
    candidate_id: str
    full_name: Optional[str] = None
    emails: List[str] = field(default_factory=list)
    phones: List[str] = field(default_factory=list)
    location: Optional[Dict[str, Any]] = None  # {city, region, country}
    links: Dict[str, Any] = field(default_factory=lambda: {
        "linkedin": None, "github": None, "portfolio": None, "other": []
    })
    headline: Optional[str] = None
    years_experience: Optional[float] = None
    skills: List[Dict[str, Any]] = field(default_factory=list)  # [{name, confidence, sources}]
    experience: List[Dict[str, Any]] = field(default_factory=list)
    education: List[Dict[str, Any]] = field(default_factory=list)
    provenance: Dict[str, Any] = field(default_factory=dict)  # {field: {source, method}}
    overall_confidence: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        from dataclasses import asdict
        return asdict(self)