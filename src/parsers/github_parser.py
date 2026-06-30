import requests
from typing import Dict, Any, Optional, List

GITHUB_API = "https://api.github.com"


def parse_github(username_or_url: str) -> Optional[Dict[str, Any]]:
    """Fetches profile + repos, aggregates languages. Raw mapping only, no normalization."""
    username = _extract_username(username_or_url)
    if not username:
        return None

    try:
        profile = _fetch(f"{GITHUB_API}/users/{username}")
        if not profile:
            return None

        repos = _fetch(f"{GITHUB_API}/users/{username}/repos?per_page=100&sort=updated") or []
        languages = _extract_languages(repos)

        return {
            "full_name": profile.get("name") or None,
            "emails": [profile["email"]] if profile.get("email") else [],
            "phones": [],
            "headline": profile.get("bio") or None,
            "current_company": profile.get("company") or None,
            "location_raw": profile.get("location") or None,
            "links": {
                "linkedin": None,
                "github": profile.get("html_url"),
                "portfolio": profile.get("blog") or None,
                "other": []
            },
            "years_experience": None,
            "skills_raw": languages,
            "experience": [],
            "education": [],
            "_meta": {
                "followers": profile.get("followers"),
                "public_repos": profile.get("public_repos")
            },
            "_source": "github",
            "_raw": profile
        }
    except requests.RequestException as e:
        print(f"[github_parser] Network error for {username}: {e}")
        return None
    except Exception as e:
        print(f"[github_parser] Failed for {username}: {e}")
        return None


def _extract_username(url: str) -> Optional[str]:
    if not url:
        return None
    url = url.strip().rstrip("/")
    if "github.com/" in url:
        return url.split("github.com/")[-1].split("/")[0] or None
    return url or None


def _fetch(url: str) -> Optional[Any]:
    resp = requests.get(url, headers={"Accept": "application/vnd.github+json"}, timeout=10)
    return resp.json() if resp.status_code == 200 else None


def _extract_languages(repos: List[dict]) -> List[str]:
    lang_counts: Dict[str, int] = {}
    for repo in repos:
        lang = repo.get("language")
        if lang:
            lang_counts[lang] = lang_counts.get(lang, 0) + 1
    return sorted(lang_counts, key=lang_counts.get, reverse=True)[:10]