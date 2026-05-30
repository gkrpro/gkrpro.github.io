"""
Shared types and HTTP helpers for evidence fetchers.

Every fetcher returns a FetchResult. The collector merges these into the model
record with provenance fields so the dashboard can show the user the source
and the verification mode (auto vs manual).
"""

from __future__ import annotations

import hashlib
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional
from urllib.parse import urlparse

import requests

log = logging.getLogger("fetchers")

# Source allowlist — any URL not matching one of these hosts is refused
ALLOWED_DOMAINS = {
    # EU regulatory
    "digital-strategy.ec.europa.eu",
    "ec.europa.eu",
    "artificialintelligenceact.eu",
    "code-of-practice.ai",
    # Independent ecosystem hubs
    "huggingface.co",
    "api.github.com",
    "github.com",
    "raw.githubusercontent.com",
    "aisi.gov.uk",
    "crfm.stanford.edu",
    # Provider trust centres (extend as fetchers are added)
    "anthropic.com",
    "trust.anthropic.com",
    "openai.com",
    "trust.openai.com",
    "deepmind.google",
    "cloud.google.com",
    "trust.google.com",
    "mistral.ai",
    "trust.mistral.ai",
    "cohere.com",
    "trust.cohere.com",
    "x.ai",
    "deepseek.com",
    "ibm.com",
    "trust.ibm.com",
}


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def today_str() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def host_allowed(url: str) -> bool:
    if not url:
        return False
    host = (urlparse(url).hostname or "").lower()
    return any(host == d or host.endswith("." + d) for d in ALLOWED_DOMAINS)


def content_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8", errors="replace")).hexdigest()[:16]


@dataclass
class FetchResult:
    """
    Outcome of fetching one evidence cell.

    value: 0 = not found, 1 = available, 2 = partial, 3 = N/A
    confidence: 'high' | 'medium' | 'low' — how sure the fetcher is
    error: human-readable error if the fetch failed (value then stays None)
    """
    value: Optional[int] = None
    source_url: Optional[str] = None
    content_hash: Optional[str] = None
    confidence: str = "high"
    note: Optional[str] = None
    error: Optional[str] = None
    captured_at: str = field(default_factory=now_iso)


class HttpClient:
    """
    Allowlist-enforcing HTTP client with sane defaults and retries.
    All fetchers share one instance per run.
    """

    def __init__(self, hf_token: Optional[str] = None, gh_token: Optional[str] = None,
                 timeout: int = 20, max_retries: int = 2):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "ai-evidence-dashboard/1.0 (+https://gkrpro.github.io/ai-evidence/)",
            "Accept": "application/json, text/html;q=0.9, */*;q=0.5",
        })
        self.hf_token = hf_token
        self.gh_token = gh_token
        self.timeout = timeout
        self.max_retries = max_retries

    def get(self, url: str, accept: Optional[str] = None) -> Optional[requests.Response]:
        if not host_allowed(url):
            log.warning("REFUSED non-allowlisted URL: %s", url)
            return None

        headers = {}
        host = (urlparse(url).hostname or "").lower()
        if host.endswith("huggingface.co") and self.hf_token:
            headers["Authorization"] = f"Bearer {self.hf_token}"
        elif host.endswith("api.github.com") and self.gh_token:
            headers["Authorization"] = f"Bearer {self.gh_token}"
            headers["X-GitHub-Api-Version"] = "2022-11-28"
            headers["Accept"] = accept or "application/vnd.github+json"
        elif accept:
            headers["Accept"] = accept

        last_err = None
        for attempt in range(self.max_retries + 1):
            try:
                r = self.session.get(url, headers=headers, timeout=self.timeout)
                if r.status_code == 429:
                    # rate-limited; back off
                    wait = min(2 ** attempt, 8)
                    log.warning("429 on %s, sleeping %ds", url, wait)
                    time.sleep(wait)
                    continue
                if r.status_code >= 500:
                    wait = 2 ** attempt
                    log.warning("%d on %s, retrying in %ds", r.status_code, url, wait)
                    time.sleep(wait)
                    continue
                return r
            except requests.RequestException as e:
                last_err = e
                if attempt < self.max_retries:
                    time.sleep(2 ** attempt)
                else:
                    log.warning("Fetch failed %s: %s", url, e)
        if last_err:
            log.warning("Giving up on %s: %s", url, last_err)
        return None
