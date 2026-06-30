import sys, os, csv
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.pipeline import run_pipeline

TEST_CONFIG = {
    "fields": [
        {"path": "full_name", "type": "string", "required": True},
        {"path": "emails", "type": "string[]", "required": True}
    ],
    "include_confidence": True,
    "include_provenance": False,
    "on_missing": "null"
}


def test_pipeline_does_not_crash_on_malformed_row(tmp_path):
    csv_path = tmp_path / "malformed.csv"
    csv_path.write_text(
        "name,email,phone,current_company,title,github_url,linkedin_url,years_experience\n"
        "Bad Entry,not-an-email,000,,,,,\n"
    )
    results = run_pipeline(str(csv_path), TEST_CONFIG)
    assert len(results) == 1
    # should produce an output dict, not raise an exception
    assert "candidate_id" in results[0]

def test_pipeline_handles_missing_github_url(tmp_path):
    """A candidate with no GitHub URL should still produce a valid profile."""
    csv_path = tmp_path / "no_github.csv"
    csv_path.write_text(
        "name,email,phone,current_company,title,github_url,linkedin_url,years_experience\n"
        "No Github,nogithub@test.com,9876543210,Acme,Engineer,,,2\n"
    )
    results = run_pipeline(str(csv_path), TEST_CONFIG)
    assert len(results) == 1
    assert results[0]["full_name"] == "No Github"
    assert results[0]["emails"] == ["nogithub@test.com"]

def test_pipeline_empty_csv_returns_empty_list(tmp_path):
    csv_path = tmp_path / "empty.csv"
    csv_path.write_text("name,email,phone,current_company,title,github_url,linkedin_url,years_experience\n")
    results = run_pipeline(str(csv_path), TEST_CONFIG)
    assert results == []


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])