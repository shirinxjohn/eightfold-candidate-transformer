import csv
import uuid
from typing import List, Dict, Any


def parse_csv(filepath: str) -> List[Dict[str, Any]]:
    """Reads CSV, maps columns to canonical field names. No normalization, no merging."""
    records = []
    try:
        with open(filepath, newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                record = {
                    "candidate_id": str(uuid.uuid4()),
                    "full_name": row.get("name") or None,
                    "emails": [row["email"]] if row.get("email") else [],
                    "phones": [row["phone"]] if row.get("phone") else [],
                    "headline": row.get("title") or None,
                    "current_company": row.get("current_company") or None,
                    "location_raw": None,  # CSV sample has no location column
                    "links": {
                        "linkedin": row.get("linkedin_url") or None,
                        "github": row.get("github_url") or None,
                        "portfolio": None,
                        "other": []
                    },
                    "years_experience": row.get("years_experience") or None,
                    "skills_raw": [],
                    "experience": [],
                    "education": [],
                    "_source": "recruiter_csv",
                    "_raw": dict(row)
                }
                records.append(record)
    except FileNotFoundError:
        print(f"[csv_parser] File not found: {filepath}")
    except Exception as e:
        print(f"[csv_parser] Failed to parse {filepath}: {e}")
    return records