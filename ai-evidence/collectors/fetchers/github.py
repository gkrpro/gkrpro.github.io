"""
GitHub fetcher.

What it checks:
  - `vd` (vulnerability disclosure): does the repo have a SECURITY.md
    or a security policy enabled?

The model record must include a `gh_repo` field (e.g. "meta-llama/llama-models")
for this fetcher to run. Without it, the field stays manual.

API: https://api.github.com/repos/{owner}/{repo}
     https://api.github.com/repos/{owner}/{repo}/contents/SECURITY.md
"""

from __future__ import annotations

import logging
from typing import Optional

from . import FetchResult, HttpClient, content_hash, today_str

log = logging.getLogger("fetchers.gh")


def _repo_api_url(repo: str) -> str:
    return f"https://api.github.com/repos/{repo}"


def _security_md_url(repo: str) -> str:
    return f"https://api.github.com/repos/{repo}/contents/SECURITY.md"


def _security_policy_url(repo: str) -> str:
    # GitHub's security policy endpoint (requires Accept header)
    return f"https://api.github.com/repos/{repo}/community/profile"


def fetch_vulnerability_disclosure(http: HttpClient, model: dict) -> FetchResult:
    repo = model.get("gh_repo")
    if not repo:
        return FetchResult(error="no gh_repo")

    # First, confirm the repo exists
    repo_resp = http.get(_repo_api_url(repo))
    if repo_resp is None or repo_resp.status_code != 200:
        status = repo_resp.status_code if repo_resp else "no-response"
        return FetchResult(error=f"gh repo fetch {status}")

    try:
        repo_data = repo_resp.json()
    except ValueError as e:
        return FetchResult(error=f"gh repo json parse: {e}")

    # Repo URL for the source link
    page_url = repo_data.get("html_url", f"https://github.com/{repo}")

    # Check for SECURITY.md
    sec_resp = http.get(_security_md_url(repo))
    if sec_resp is not None and sec_resp.status_code == 200:
        return FetchResult(
            value=1,
            source_url=f"{page_url}/blob/{repo_data.get('default_branch', 'main')}/SECURITY.md",
            captured_at=today_str(),
            note="SECURITY.md present",
        )

    # Fallback: community profile (counts security policy enablement)
    profile_resp = http.get(_security_policy_url(repo))
    if profile_resp is not None and profile_resp.status_code == 200:
        try:
            profile = profile_resp.json()
            files = profile.get("files", {}) or {}
            sec_policy = files.get("security") if isinstance(files, dict) else None
            if sec_policy:
                # GitHub reports the security policy file as present
                sec_url = sec_policy.get("html_url") if isinstance(sec_policy, dict) else None
                return FetchResult(
                    value=1,
                    source_url=sec_url or f"{page_url}/security/policy",
                    captured_at=today_str(),
                    note="security policy registered in community profile",
                )
        except ValueError:
            pass

    return FetchResult(
        value=0,
        source_url=page_url,
        captured_at=today_str(),
        note="no SECURITY.md or registered security policy",
    )
