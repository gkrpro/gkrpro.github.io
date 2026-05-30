#!/usr/bin/env python3
"""
Evidence collector for the AI Model Security Evidence dashboard.

Reads data/models.json, refreshes evidence cells from public sources,
writes back the updated JSON, and emits per-run audit logs.

This is a SKELETON. The fetchers are stubs that return current values
unchanged with refreshed timestamps. Implement the real fetchers per
provider (see PROVIDER_FETCHERS below) before going live.

Design principles:
  - Only fetch from the source allowlist (provider domains, HF, GitHub,
    EU AI Office).
  - One closed question per cell; output is 0/1/2/3 only.
  - Every change logged with source_url, captured_at, content_hash.
  - On any fetch failure, keep the previous value and mark stale.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import logging
import os
import sys
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

# Source allowlist — fetches outside this list are refused
ALLOWED_DOMAINS = {
    # EU
    "digital-strategy.ec.europa.eu",
    "artificialintelligenceact.eu",
    "code-of-practice.ai",
    # Providers (extend as needed)
    "anthropic.com",
    "trust.anthropic.com",
    "openai.com",
    "trust.openai.com",
    "deepmind.google",
    "cloud.google.com",
    "mistral.ai",
    "trust.mistral.ai",
    "cohere.com",
    "x.ai",
    "deepseek.com",
    # Independent
    "huggingface.co",
    "api.github.com",
    "github.com",
    "aisi.gov.uk",
    "crfm.stanford.edu",
}


@dataclass
class FetchResult:
    value: int  # 0 = not found, 1 = available, 2 = partial, 3 = N/A
    source_url: str | None
    content_hash: str | None
    note: str | None = None


def host_allowed(url: str) -> bool:
    if not url:
        return False
    host = urlparse(url).hostname or ""
    return any(host == d or host.endswith("." + d) for d in ALLOWED_DOMAINS)


def safe_get(url: str, timeout: int = 15) -> requests.Response | None:
    if not host_allowed(url):
        log.warning("Refused non-allowlisted URL: %s", url)
        return None
    try:
        r = requests.get(url, timeout=timeout, headers={
            "User-Agent": "ai-evidence-dashboard/0.1 (+https://example.org)"
        })
        r.raise_for_status()
        return r
    except requests.RequestException as e:
        log.warning("Fetch failed %s: %s", url, e)
        return None


def content_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


# ---------------------------------------------------------------------------
# Per-question fetchers (stubs — implement per provider)
# ---------------------------------------------------------------------------

def fetch_model_card(model: dict) -> FetchResult:
    """Check if a model card exists on HF or provider site."""
    # Try HuggingFace first for open-weight models
    if model.get("o") == "Open-weight":
        slug = model.get("hf_slug")
        if slug:
            r = safe_get(f"https://huggingface.co/api/models/{slug}")
            if r and r.ok:
                return FetchResult(1, f"https://huggingface.co/{slug}", content_hash(r.text))
    # Fallback: keep prior value, do not invent a source
    return FetchResult(model.get("mc", 0), None, None, "skeleton: no provider fetcher implemented")


def fetch_cop_signatory(model: dict) -> FetchResult:
    """Check CoP signatory list from the EU AI Office."""
    # Production: parse https://digital-strategy.ec.europa.eu/en/policies/contents-code-gpai
    # Skeleton: return prior value unchanged
    return FetchResult(model.get("cop", "N"), None, None, "skeleton: parse CoP page")


def fetch_soc2(model: dict) -> FetchResult:
    """Check provider trust centre for SOC 2."""
    return FetchResult(model.get("s2", 0), None, None, "skeleton: per-provider trust page")


def fetch_iso27001(model: dict) -> FetchResult:
    return FetchResult(model.get("iso", 0), None, None, "skeleton: per-provider trust page")


# Map evidence-cell keys to fetcher functions
FETCHERS: dict[str, Callable[[dict], FetchResult]] = {
    "mc": fetch_model_card,
    "s2": fetch_soc2,
    "iso": fetch_iso27001,
    # Extend: sc, td, se, tp, rt, vd, dpa, eu, nt
}


# Per-provider fetcher modules can be added here for source URLs that
# vary by vendor (Anthropic Trust Portal vs OpenAI Trust vs Google Cloud)
PROVIDER_FETCHERS: dict[str, dict] = {
    # Example structure:
    # "Anthropic": {"s2": "https://trust.anthropic.com/...", "iso": "..."},
}


def refresh_model(model: dict, audit_dir: Path) -> dict:
    """Run all fetchers for one model; log changes."""
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    changes = []
    for key, fetcher in FETCHERS.items():
        prior = model.get(key)
        try:
            result = fetcher(model)
        except Exception as e:  # never let a fetcher crash the run
            log.error("Fetcher %s failed for %s: %s", key, model.get("n"), e)
            continue
        if result.value != prior:
            changes.append({
                "field": key,
                "from": prior,
                "to": result.value,
                "source_url": result.source_url,
                "content_hash": result.content_hash,
                "note": result.note,
            })
            model[key] = result.value
        if result.source_url:
            model.setdefault("urls", {})[key] = result.source_url

    model["last_verified"] = now[:10]

    if changes:
        audit_dir.mkdir(parents=True, exist_ok=True)
        log_path = audit_dir / f"{model['n'].replace(' ', '_').replace('/', '_')}.jsonl"
        with log_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps({"timestamp": now, "changes": changes}) + "\n")
        log.info("Updated %s: %d field(s) changed", model["n"], len(changes))

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
    log.info("Refreshing %d models", len(models))

    for m in models:
        refresh_model(m, audit_dir)

    payload["meta"] = payload.get("meta", {})
    payload["meta"]["generated_at"] = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    payload["meta"]["generator"] = "collectors/refresh.py"

    out_path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    log.info("Wrote %s", out_path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
