"""
EU AI Office Code of Practice signatory fetcher.

Source: https://digital-strategy.ec.europa.eu/en/policies/contents-code-gpai
Fallback / cross-reference: https://artificialintelligenceact.eu/introduction-to-code-of-practice/

The official EU page lists signatories by company name. We parse the HTML for
known signatory names and resolve them against the model's `p` (provider) field.

This fetcher is run *per provider* (cached across all models from that provider
in a single run) — the registry is provider-level, not model-level.

Outcome cell `cop`:
  "F" — Full signatory (Transparency + Copyright + Safety/Security chapters)
  "S" — Safety & Security chapter only (notably xAI as of 2025)
  "N" — Not a signatory

NOTE: Currently the EU AI Office page does not differentiate "Safety chapter only"
signatories within the main signatory list — that information lives in separate
press releases. So this fetcher returns "F" or "N", and the "S" case stays
manually curated for now (with the `manually_verified` flag set).
"""

from __future__ import annotations

import logging
import re
from typing import Optional

from . import FetchResult, HttpClient, content_hash, today_str

log = logging.getLogger("fetchers.cop")

# Primary URL (parsed first); fallback secondary if primary fails
COP_PRIMARY_URL = "https://digital-strategy.ec.europa.eu/en/policies/contents-code-gpai"
COP_FALLBACK_URL = "https://artificialintelligenceact.eu/introduction-to-code-of-practice/"

# Map provider names (as they appear in models.json) to the canonical signatory
# string the EU page uses. Keep this conservative — only entries we are
# confident in. New providers default to "not found" until added here.
PROVIDER_TO_SIGNATORY = {
    "Anthropic": "Anthropic",
    "OpenAI": "OpenAI",
    "Google": "Google",
    "Google DeepMind": "Google",
    "Microsoft": "Microsoft",
    "IBM": "IBM",
    "Cohere": "Cohere",
    "Mistral AI": "Mistral AI",
    "Mistral / NVIDIA": "Mistral AI",
    "Aleph Alpha": "Aleph Alpha",
    "Amazon": "Amazon",
    "ServiceNow": "ServiceNow",
    # Known non-signatories (kept for explicit reporting):
    "Meta": None,
    "xAI": None,         # signed Safety chapter only — stays manual
    "DeepSeek": None,
    "Alibaba": None,
    "Z.AI": None,
    "MiniMax": None,
    "Moonshot": None,
    "01.AI": None,
    "Shanghai AI Lab": None,
    "Reka": None,
    "Inflection": None,
    "AI21 Labs": None,
    "Perplexity": None,
    "TII": None,
    "Databricks": None,
    "AI2": None,
    "Stability AI": None,
    "MosaicML": None,
    "BigScience": None,
    "Nous Research": None,
    "NVIDIA": None,
}


class CoPSignatoryIndex:
    """
    One-shot fetch + parse of the EU AI Office CoP signatories page.
    Resolves provider -> signatory status. Cached for the lifetime of one
    collector run.
    """

    def __init__(self, http: HttpClient):
        self._http = http
        self._signatories: Optional[set[str]] = None
        self._source_url: Optional[str] = None
        self._content_hash: Optional[str] = None
        self._error: Optional[str] = None

    def _parse(self, html: str) -> set[str]:
        """
        The signatories list is rendered as bullet points on the page.
        We extract candidate names and validate against our allowlist of
        known providers to avoid false positives from page chrome.
        """
        # Extract anything that looks like a list item or paragraph word
        # Names we look for are the canonical signatory strings.
        found: set[str] = set()
        known_names = {v for v in PROVIDER_TO_SIGNATORY.values() if v}
        for name in known_names:
            # Use word boundaries; case-insensitive
            pattern = r"(?:^|[\s>\(\-\[])" + re.escape(name) + r"(?:[\s<\)\.\,\;\!\?\-\]]|$)"
            if re.search(pattern, html, re.IGNORECASE):
                found.add(name)
        return found

    def load(self) -> bool:
        """Fetch and parse the signatory list. Returns True on success."""
        if self._signatories is not None:
            return True
        if self._error is not None:
            return False

        for url in (COP_PRIMARY_URL, COP_FALLBACK_URL):
            resp = self._http.get(url, accept="text/html")
            if resp is None or resp.status_code != 200:
                continue
            html = resp.text
            parsed = self._parse(html)
            if not parsed:
                # Don't accept an empty parse — page structure changed
                log.warning("CoP signatory parse returned 0 names from %s", url)
                continue
            self._signatories = parsed
            self._source_url = url
            self._content_hash = content_hash(html)
            log.info("CoP signatories loaded from %s: %d found", url, len(parsed))
            return True

        self._error = "all CoP source URLs failed or returned no parseable signatories"
        return False

    def status_for(self, provider: str) -> FetchResult:
        if not self.load():
            return FetchResult(error=self._error or "CoP index not loaded")

        canonical = PROVIDER_TO_SIGNATORY.get(provider)
        if canonical is None:
            # Either an unknown provider (we can't claim a status) OR a known
            # non-signatory. Treat unknown as low confidence.
            if provider in PROVIDER_TO_SIGNATORY:
                return FetchResult(
                    value=None,   # value is for numeric fields; cop is a string
                    source_url=self._source_url,
                    content_hash=self._content_hash,
                    captured_at=today_str(),
                    note=f"{provider}: known non-signatory",
                )
            return FetchResult(
                error=f"provider '{provider}' not in PROVIDER_TO_SIGNATORY map",
                confidence="low",
            )

        is_signatory = canonical in self._signatories
        return FetchResult(
            value=None,
            source_url=self._source_url,
            content_hash=self._content_hash,
            captured_at=today_str(),
            note=("F" if is_signatory else "N") + f" ({canonical})",
        )


def fetch_cop_status(index: CoPSignatoryIndex, model: dict) -> tuple[Optional[str], FetchResult]:
    """
    Returns the new cop value ('F' / 'N' / None for unknown) and the FetchResult.
    The collector uses the value to update model['cop'].
    """
    provider = model.get("p", "")
    result = index.status_for(provider)
    if result.error:
        return None, result

    canonical = PROVIDER_TO_SIGNATORY.get(provider)
    if canonical is None:
        # Known non-signatory in our map
        if provider in PROVIDER_TO_SIGNATORY:
            return "N", result
        # Truly unknown — leave unchanged
        return None, result

    is_signatory = canonical in (index._signatories or set())
    return ("F" if is_signatory else "N"), result
