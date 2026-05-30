"""
Hugging Face fetcher.

What it checks:
  - `mc` (model card): does a model card exist with non-trivial content?
  - `td` (training data disclosure): does the card describe training data?

API: https://huggingface.co/api/models/{org}/{slug}
     https://huggingface.co/api/models/{org}/{slug}?blobs=true

The model record must include an `hf_slug` field (e.g. "meta-llama/Llama-3.3-70B-Instruct")
for this fetcher to run; otherwise it returns a no-op result and the field stays manual.
"""

from __future__ import annotations

import logging
import re
from typing import Optional

from . import FetchResult, HttpClient, content_hash, today_str

log = logging.getLogger("fetchers.hf")

# Heuristic markers that indicate a *real* model card vs an empty stub.
# A card is "partial" if it exists but is short or unstructured; "available"
# if it has at least 3 of these substantive markers.
CARD_MARKERS = [
    r"\bmodel\s*details?\b",
    r"\bintended\s*use",
    r"\blimitations?\b",
    r"\bevaluation\b",
    r"\btraining\s*data\b",
    r"\bperformance\b",
    r"\bbenchmark",
    r"\bsafety\b",
    r"\brisks?\b",
    r"\bbias(es)?\b",
]

TRAINING_DATA_MARKERS = [
    r"\btraining\s*data\b",
    r"\btraining\s*set\b",
    r"\bdataset[s]?\b",
    r"\bcorpus\b",
    r"\bpretraining\b",
    r"\bpre-training\b",
]


def _readme_url(slug: str) -> str:
    # HF serves the README from the model repo via huggingface.co/{slug}/raw/main/README.md
    return f"https://huggingface.co/{slug}/raw/main/README.md"


def _api_url(slug: str) -> str:
    return f"https://huggingface.co/api/models/{slug}"


def _count_markers(text: str, patterns: list[str]) -> int:
    text_l = text.lower()
    return sum(1 for p in patterns if re.search(p, text_l, re.IGNORECASE))


def fetch_model_card(http: HttpClient, model: dict) -> FetchResult:
    slug = model.get("hf_slug")
    if not slug:
        return FetchResult(error="no hf_slug")

    api_resp = http.get(_api_url(slug))
    if api_resp is None or api_resp.status_code != 200:
        status = api_resp.status_code if api_resp else "no-response"
        return FetchResult(error=f"hf api {status}")

    try:
        meta = api_resp.json()
    except ValueError as e:
        return FetchResult(error=f"hf api json parse: {e}")

    # The model page URL is the canonical user-facing source
    page_url = f"https://huggingface.co/{slug}"

    # First, see if there is any model card at all by checking cardData
    has_card_data = bool(meta.get("cardData"))

    # Then fetch the README to inspect actual content
    readme_resp = http.get(_readme_url(slug))
    readme_text = ""
    if readme_resp and readme_resp.status_code == 200:
        readme_text = readme_resp.text

    if not has_card_data and not readme_text.strip():
        return FetchResult(
            value=0,
            source_url=page_url,
            captured_at=today_str(),
            note="no model card",
        )

    # Score the README content
    marker_count = _count_markers(readme_text, CARD_MARKERS) if readme_text else 0
    length = len(readme_text)

    if marker_count >= 3 and length > 1500:
        value = 1
        note = f"{marker_count} markers, {length} chars"
    elif marker_count >= 1 or length > 500:
        value = 2
        note = f"partial: {marker_count} markers, {length} chars"
    else:
        value = 2 if has_card_data else 0
        note = "card-data only, no substantive README"

    return FetchResult(
        value=value,
        source_url=page_url,
        content_hash=content_hash(readme_text) if readme_text else None,
        captured_at=today_str(),
        note=note,
    )


def fetch_training_data_disclosure(http: HttpClient, model: dict) -> FetchResult:
    """
    Checks the README/model card for any disclosure of training data.

    1 = explicitly describes datasets, corpora, or training data sources
    2 = mentions training data generally but no specifics
    0 = no mention
    """
    slug = model.get("hf_slug")
    if not slug:
        return FetchResult(error="no hf_slug")

    readme_resp = http.get(_readme_url(slug))
    if readme_resp is None or readme_resp.status_code != 200:
        return FetchResult(error="readme not fetched")

    text = readme_resp.text
    page_url = f"https://huggingface.co/{slug}"

    marker_count = _count_markers(text, TRAINING_DATA_MARKERS)
    if marker_count == 0:
        return FetchResult(
            value=0,
            source_url=page_url,
            captured_at=today_str(),
            note="no training-data section detected",
        )

    # Heuristic: look for named datasets (common patterns)
    has_named_dataset = bool(re.search(
        r"\b(C4|Common\s*Crawl|RedPajama|RefinedWeb|Pile|Wikipedia|"
        r"FineWeb|Books|GitHub|StarCoder|arXiv|Reddit|StackExchange|"
        r"DCLM|Dolma|RedPajama-Data)\b",
        text, re.IGNORECASE,
    ))

    if has_named_dataset:
        value = 1
        note = f"{marker_count} markers, named datasets present"
    else:
        value = 2
        note = f"{marker_count} markers, generic mention only"

    return FetchResult(
        value=value,
        source_url=page_url,
        content_hash=content_hash(text),
        captured_at=today_str(),
        note=note,
    )
