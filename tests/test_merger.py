import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.merger.merger import merge


def test_merge_prefers_csv_over_github_for_scalar_fields():
    """CSV should win for full_name when both sources disagree — priority policy."""
    csv_record = {
        "full_name": "Jane Doe", "headline": "Software Engineer", "years_experience": 4.0,
        "emails": [], "phones": [], "links": {"linkedin": None, "github": None, "portfolio": None, "other": []},
        "location": None, "skills_raw": [], "_source": "recruiter_csv"
    }
    github_record = {
        "full_name": "J. Doe", "headline": "Backend Dev @ Google", "years_experience": None,
        "emails": [], "phones": [], "links": {"linkedin": None, "github": None, "portfolio": None, "other": []},
        "location": None, "skills_raw": [], "_source": "github"
    }
    candidate = merge([csv_record, github_record], "test-id-1")
    assert candidate.full_name == "Jane Doe"
    assert candidate.provenance["full_name"]["source"] == "recruiter_csv"

def test_merge_falls_back_to_github_when_csv_missing_field():
    """If CSV has no headline, GitHub's should be used instead."""
    csv_record = {
        "full_name": "Jane Doe", "headline": None, "years_experience": None,
        "emails": [], "phones": [], "links": {"linkedin": None, "github": None, "portfolio": None, "other": []},
        "location": None, "skills_raw": [], "_source": "recruiter_csv"
    }
    github_record = {
        "full_name": None, "headline": "Backend Dev @ Google", "years_experience": None,
        "emails": [], "phones": [], "links": {"linkedin": None, "github": None, "portfolio": None, "other": []},
        "location": None, "skills_raw": [], "_source": "github"
    }
    candidate = merge([csv_record, github_record], "test-id-2")
    assert candidate.headline == "Backend Dev @ Google"
    assert candidate.provenance["headline"]["source"] == "github"

def test_merge_unions_emails_from_both_sources():
    csv_record = {
        "full_name": "Jane Doe", "headline": None, "years_experience": None,
        "emails": ["jane@gmail.com"], "phones": [],
        "links": {"linkedin": None, "github": None, "portfolio": None, "other": []},
        "location": None, "skills_raw": [], "_source": "recruiter_csv"
    }
    github_record = {
        "full_name": None, "headline": None, "years_experience": None,
        "emails": ["jane.doe@work.com"], "phones": [],
        "links": {"linkedin": None, "github": None, "portfolio": None, "other": []},
        "location": None, "skills_raw": [], "_source": "github"
    }
    candidate = merge([csv_record, github_record], "test-id-3")
    assert set(candidate.emails) == {"jane@gmail.com", "jane.doe@work.com"}

def test_merge_handles_single_source_gracefully():
    """No crash when only CSV is present (e.g. GitHub fetch failed)."""
    csv_record = {
        "full_name": "Solo Candidate", "headline": "Engineer", "years_experience": 2.0,
        "emails": ["solo@test.com"], "phones": [],
        "links": {"linkedin": None, "github": None, "portfolio": None, "other": []},
        "location": None, "skills_raw": [], "_source": "recruiter_csv"
    }
    candidate = merge([csv_record], "test-id-4")
    assert candidate.full_name == "Solo Candidate"
    assert candidate.emails == ["solo@test.com"]


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])