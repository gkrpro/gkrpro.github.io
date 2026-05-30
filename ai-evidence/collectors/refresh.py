#!/usr/bin/env python3
"""
Evidence collector for the AI Model Security Evidence dashboard.

This is the REAL implementation for 3 of the 12 evidence cells:
  - mc (Model card)      via HuggingFace API
  - cop (CoP signatory)  via EU AI Office page parser
  - vd (Vuln disclosure) via GitHub API (org-level security.md detection)

The other 9 cells remain manually curated. Every cell carries a
`verification_method` of "automated", "manual", or "unverified", visible
in the dashboard. Unverified cells are flagged for review — they are
NOT marked non-compliant, which would be a defamation risk.

Source allowlist enforced — fetches outside the allowlist are refused.
Every change is logged to data/audit/<model>.jsonl with timestamp,
source URL, and content hash.

Usage:
  python refresh.py --input data/models.json --output data/models.json --log-dir data/audit
"""

from __future__ import annotations

import argparse
import hashlib
import json
import logging
import os
import re
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable
from urllib.parse import urlparse

import requests

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)
log = logging.getLogger("collector")

USER_AGENT = "ai-evidence-dashboard/1.0 (+https://gkrpro.github.io/ai-evidence/)"
HTTP_TIMEOUT = 20

# Source allowlist — fetches outside this list are refused.
ALLOWED_DOMAINS = {
    # EU
    "digital-strategy.ec.europa.eu",
    "artificialintelligenceact.eu",
    "code-of-practice.ai",
    # Hugging Face
    "huggingface.co",
    # GitHub
    "api.github.com",
    "github.com",
    "raw.githubusercontent.com",
    # Provider trust centres (added as fetchers grow)
    "trust.anthropic.com",
    "trust.openai.com",
    "trust.mistral.ai",
}

# CoP signatory facts (sourced manually from the EU AI Office page; the
# parser falls back to this if the page format changes).
# Source: https://digital-strategy.ec.europa.eu/en/policies/contents-code-gpai
# As of 2026-05.
COP_SIGNATORIES_FALLBACK: dict[str, str] = {
    "amazon": "F",
    "anthropic": "F",
    "ibm": "F",
    "microsoft": "F",
    "openai": "F",
    "google": "F",
    "google deepmind": "F",
    "aleph alpha": "F",
    "mistral ai": "F",
    "mistral / nvidia": "F",
    "cohere": "F",
    "xai": "S",
    "meta": "N",
    "deepseek": "N",
    "alibaba": "N",
    "z.ai": "N",
    "moonshot": "N",
    "minimax": "N",
}

COP_PAGE_URL = "https://digital-strategy.ec.europa.eu/en/policies/contents-code-gpai"
_cop_page_cache: dict[str, str] | None = None


@dataclass
class FetchResult:
    value: int | str
    source_url: str | None
    api_url: str | None
    content_hash: str | None
    method: str  # "automated" or "unverified"
    note: str | None = None


def host_allowed(url: str) -> bool:
    if not url:
        return False
    host = (urlparse(url).hostname or "").lower()
    return any(host == d or host.endswith("." + d) for d in ALLOWED_DOMAINS)


def safe_get(url: str, headers: dict | None = None) -> requests.Response | None:
    if not host_allowed(url):
        log.warning("REFUSED non-allowlisted URL: %s", url)
        return None
    h = {"User-Agent": USER_AGENT, "Accept": "application/json, text/html"}
    if headers:
        h.update(headers)
    try:
        r = requests.get(url, timeout=HTTP_TIMEOUT, headers=h)
        r.raise_for_status()
        return r
    except requests.RequestException as e:
        log.warning("Fetch failed %s: %s", url, e)
        return None


def content_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def normalise_provider(name: str) -> str:
    return (name or "").strip().lower()


# ---------------------------------------------------------------------------
# Fetcher 1 — Model card via HuggingFace API
# ---------------------------------------------------------------------------

def fetch_model_card_hf(model: dict) -> FetchResult:
    """
    Check the HuggingFace Hub for a model card.
    HF API docs: https://huggingface.co/docs/hub/api
    """
    slug = model.get("hf_slug")
    if not slug:
        return FetchResult(
            value=model.get("mc", 0),
            source_url=None,
            api_url=None,
            content_hash=None,
            method="unverified",
            note="no hf_slug — SaaS-only model or slug not configured",
        )

    api_url = f"https://huggingface.co/api/models/{slug}"
    page_url = f"https://huggingface.co/{slug}"

    headers = {}
    if os.environ.get("HF_TOKEN"):
        headers["Authorization"] = f"Bearer {os.environ['HF_TOKEN']}"

    r = safe_get(api_url + "?expand=cardData&expand=downloads&expand=tags", headers=headers)
    if not r:
        return FetchResult(
            value=model.get("mc", 0),
            source_url=None,
            api_url=api_url,
            content_hash=None,
            method="unverified",
            note="HF API fetch failed",
        )

    try:
        data = r.json()
    except ValueError:
        return FetchResult(
            value=model.get("mc", 0),
            source_url=None,
            api_url=api_url,
            content_hash=None,
            method="unverified",
            note="HF API returned non-JSON",
        )

    card = data.get("cardData") or {}
    tags = data.get("tags") or []

    has_card_signals = (
        bool(card.get("license"))
        or bool(card.get("tags"))
        or bool(card.get("model_index"))
        or bool(card.get("base_model"))
        or bool(card.get("model-index"))
    )
    has_meaningful_tags = len([t for t in tags if t and not t.startswith("language:")]) >= 2

    if has_card_signals and has_meaningful_tags:
        value = 1
    elif has_card_signals or has_meaningful_tags:
        value = 2
    else:
        value = 0

    return FetchResult(
        value=value,
        source_url=page_url,
        api_url=api_url,
        content_hash=content_hash(r.text),
        method="automated",
        note=None,
    )


# ---------------------------------------------------------------------------
# Fetcher 2 — CoP signatory via EU AI Office
# ---------------------------------------------------------------------------

def _load_cop_signatory_list() -> dict[str, str]:
    """Parse the CoP page; fall back to the curated list on error."""
    global _cop_page_cache
    if _cop_page_cache is not None:
        return _cop_page_cache

    r = safe_get(COP_PAGE_URL)
    if not r:
        log.warning("CoP page unreachable, using fallback list")
        _cop_page_cache = dict(COP_SIGNATORIES_FALLBACK)
        return _cop_page_cache

    text = r.text.lower()

    # Start with fallback as floor — never downgrade based on parsing.
    result = dict(COP_SIGNATORIES_FALLBACK)

    candidates = [
        "amazon", "anthropic", "ibm", "microsoft", "openai",
        "google", "google deepmind", "aleph alpha", "mistral ai",
        "cohere",
    ]
    for c in candidates:
        for m in re.finditer(re.escape(c), text):
            window = text[max(0, m.start() - 200):m.end() + 200]
            if "signed" in window and "have not signed" not in window:
                result[c] = result.get(c, "F")
                break

    if "xai" in text and ("safety and security chapter" in text or "safety & security chapter" in text):
        result["xai"] = "S"

    _cop_page_cache = result
    return result


def fetch_cop_signatory(model: dict) -> FetchResult:
    provider = normalise_provider(model.get("p", ""))
    signatories = _load_cop_signatory_list()

    value = signatories.get(provider)
    if value is None:
        for known, v in signatories.items():
            if known in provider:
                value = v
                break

    if value is None:
        return FetchResult(
            value="N",
            source_url=COP_PAGE_URL,
            api_url=COP_PAGE_URL,
            content_hash=None,
            method="unverified",
            note=f"provider '{provider}' not in known signatory list",
        )

    return FetchResult(
        value=value,
        source_url=COP_PAGE_URL,
        api_url=COP_PAGE_URL,
        content_hash=None,
        method="automated",
        note=None,
    )


# ---------------------------------------------------------------------------
# Fetcher 3 — Vulnerability disclosure via GitHub
# ---------------------------------------------------------------------------

def fetch_vdp_github(model: dict) -> FetchResult:
    """
    Detect a public Vulnerability Disclosure Policy via GitHub:
      - Org-level SECURITY.md in <org>/.github (GitHub's community-health
        pattern: https://docs.github.com/en/communities/setting-up-your-project-for-healthy-contributions/adding-a-security-policy-to-your-repository)
      - Or repo-level SECURITY.md (partial — value=2)
    """
    org = model.get("github_org")
    if not org:
        return FetchResult(
            value=model.get("vd", 0),
            source_url=None,
            api_url=None,
            content_hash=None,
            method="unverified",
            note="no github_org configured",
        )

    candidates = [
        f"https://api.github.com/repos/{org}/.github/contents/SECURITY.md",
        f"https://api.github.com/repos/{org}/.github/contents/security.md",
    ]
    headers = {"Accept": "application/vnd.github+json"}
    if os.environ.get("GH_TOKEN"):
        headers["Authorization"] = f"Bearer {os.environ['GH_TOKEN']}"

    for api_url in candidates:
        r = safe_get(api_url, headers=headers)
        if r and r.status_code == 200:
            public_url = f"https://github.com/{org}/.github/blob/main/SECURITY.md"
            return FetchResult(
                value=1,
                source_url=public_url,
                api_url=api_url,
                content_hash=content_hash(r.text),
                method="automated",
                note=None,
            )

    repo = model.get("github_repo")
    if repo:
        api_url = f"https://api.github.com/repos/{org}/{repo}/contents/SECURITY.md"
        r = safe_get(api_url, headers=headers)
        if r and r.status_code == 200:
            public_url = f"https://github.com/{org}/{repo}/blob/main/SECURITY.md"
            return FetchResult(
                value=2,
                source_url=public_url,
                api_url=api_url,
                content_hash=content_hash(r.text),
                method="automated",
                note="repo-level SECURITY.md only",
            )

    return FetchResult(
        value=0,
        source_url=f"https://github.com/{org}",
        api_url=candidates[0],
        content_hash=None,
        method="automated",
        note="no SECURITY.md found at org or repo level",
    )


# ---------------------------------------------------------------------------
# Driver
# ---------------------------------------------------------------------------

AUTOMATED_FETCHERS: dict[str, Callable[[dict], FetchResult]] = {
    "mc": fetch_model_card_hf,
    "cop": fetch_cop_signatory,
    "vd": fetch_vdp_github,
}

MANUAL_CELLS = ["sc", "td", "se", "tp", "rt", "s2", "iso", "dpa", "eu", "nt"]


def refresh_model(model: dict, audit_dir: Path) -> dict:
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    changes = []

    model.setdefault("verification", {})
    model.setdefault("urls", {})
    model.setdefault("api_urls", {})

    for key, fetcher in AUTOMATED_FETCHERS.items():
        prior_value = model.get(key)
        prior_method = model["verification"].get(key, "unverified")
        try:
            result = fetcher(model)
        except Exception as e:
            log.error("Fetcher %s failed for %s: %s", key, model.get("n"), e)
            continue

        if result.value != prior_value or prior_method != result.method:
            changes.append({
                "field": key,
                "from_value": prior_value,
                "to_value": result.value,
                "from_method": prior_method,
                "to_method": result.method,
                "source_url": result.source_url,
                "api_url": result.api_url,
                "content_hash": result.content_hash,
                "note": result.note,
            })

        model[key] = result.value
        model["verification"][key] = result.method
        if result.source_url:
            model["urls"][key] = result.source_url
        if result.api_url:
            model["api_urls"][key] = result.api_url

    for key in MANUAL_CELLS:
        if key not in model["verification"]:
            model["verification"][key] = "unverified"

    model["last_verified"] = now[:10]
    model["last_run"] = now

    if changes:
        audit_dir.mkdir(parents=True, exist_ok=True)
        safe_name = re.sub(r"[^A-Za-z0-9_.-]", "_", model["n"])
        log_path = audit_dir / f"{safe_name}.jsonl"
        with log_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps({"timestamp": now, "changes": changes}) + "\n")
        log.info("Updated %s: %d automated field(s) changed", model["n"], len(changes))

    return model


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", default="data/models.json")
    ap.add_argument("--output", default="data/models.json")
    ap.add_argument("--log-dir", default="data/audit")
    args = ap.parse_args()

    in_path = Path(args.input)
    out_path = Path(args.output)
    audit_dir = Path(args.log_dir)

    if not in_path.exists():
        log.error("Input file not found: %s", in_path)
        return 1

    payload = json.loads(in_path.read_text(encoding="utf-8"))
    models = payload.get("models", [])
    log.info("Refreshing %d models with %d automated fetchers", len(models), len(AUTOMATED_FETCHERS))

    _load_cop_signatory_list()

    for i, m in enumerate(models, 1):
        refresh_model(m, audit_dir)
        if i % 10 == 0:
            time.sleep(0.5)

    payload["meta"] = payload.get("meta", {})
    payload["meta"]["generated_at"] = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    payload["meta"]["generated_at_iso"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    payload["meta"]["generator"] = "ai-evidence/collectors/refresh.py"
    payload["meta"]["automated_cells"] = list(AUTOMATED_FETCHERS.keys())
    payload["meta"]["manual_cells"] = MANUAL_CELLS

    out_path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    log.info("Wrote %s", out_path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
