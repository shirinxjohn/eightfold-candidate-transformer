import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.normalizers.normalizer import normalize_phone, normalize_email, normalize_skill, normalize_location


def test_normalize_phone_valid_10_digit():
    assert normalize_phone("9876543210") == "+919876543210"

def test_normalize_phone_already_has_country_code():
    assert normalize_phone("+91 98765 43210") == "+919876543210"

def test_normalize_phone_garbage_returns_none():
    assert normalize_phone("000") is None

def test_normalize_email_valid():
    assert normalize_email("JOHN@Gmail.com") == "john@gmail.com"

def test_normalize_email_invalid_returns_none():
    assert normalize_email("not-an-email") is None

def test_normalize_skill_alias():
    assert normalize_skill("js") == "JavaScript"
    assert normalize_skill("python") == "Python"

def test_normalize_location_three_parts():
    loc = normalize_location("Bengaluru, Karnataka, India")
    assert loc["city"] == "Bengaluru"
    assert loc["region"] == "Karnataka"
    assert loc["country_code"] == "IN"

def test_normalize_location_empty_returns_none():
    assert normalize_location("") is None
    assert normalize_location(None) is None


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])