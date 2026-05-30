#!/usr/bin/env python3
"""
Evidence collector orchestrator.

Reads ai-evidence/data/models.json, runs the live fetchers, and writes back
with provenance per cell. The dashboard then reads provenance to distinguish
auto-verified from manually-curated cells.

Three live fetchers ship today:
  - huggingface.fetch_model_card           -> cell `mc`
  - huggingface.fetch_training_data_disc.  -> cell `td`
  - cop.fetch_cop_status                   -> cell `cop`
  - github.fetch_vulnerability_disclosure  -> cell `vd`

(That's three live fetcher modules covering four cells. The other eight cells
stay manually curated and are explicitly marked `manually_verified` in the
provenance map. The dashboard shows the distinction.)

Provenance schema per model:
    "_provenance": {
        "mc":  {"mode": "auto",   "source_url": "...", "captured_at": "...", "note": "..."},
        "td":  {"mode": "auto",   ...},
        "cop": {"mode": "auto",   ...},
        "vd":  {"mode": "auto",   ...},
        "sc":  {"mode": "manual"},
        "se":  {"mode": "manual"},
        ...
    }

Usage:
    python refresh.py --input data/models.json --output data/models.json --log-dir data/audit
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

from fetchers import HttpClient, FetchResult, now_iso, today_str
from fetchers.huggingface import fetch_model_card, fetch_training_data_disclosure
from fetchers.cop import CoPSignatoryIndex, fetch_cop_status
from fetchers.github import fetch_vulnerability_disclosure

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
log = logging.getLogger("collector")

# Cells that have a live fetcher today. Everything else stays manual.
AUTO_FETCHED_CELLS = {"mc", "td", "cop", "vd"}

# All cells in the model schema, for provenance bookkeeping
ALL_CELLS = ["mc", "sc", "td", "se", "tp", "rt", "s2", "iso", "vd", "dpa", "eu", "nt", "cop"]


def init_provenance(model: dict) -> dict:
    """Ensure the model has a _provenance map with all cells accounted for."""
    prov = model.setdefault("_provenance", {})
    for cell in ALL_CELLS:
        if cell not in prov:
            # Default to manual for any cell that doesn't yet have provenance
            prov[cell] = {"mode": "manual", "captured_at": None}
    return prov


def record_auto(model: dict, cell: str, result: FetchResult, prior_value):
    """Update model[cell] and provenance from a successful FetchResult."""
    prov = model["_provenance"]

    if result.error:
        # Don't change the cell, but record the attempt
        prov[cell] = {
            "mode": prov.get(cell, {}).get("mode", "manual"),
            "last_auto_attempt": now_iso(),
            "last_auto_error": result.error,
            **{k: prov.get(cell, {}).get(k) for k in ("source_url", "captured_at", "note", "content_hash")},
        }
        log.info("  %s: fetcher error (%s) — keeping prior value", cell, result.error)
        return False

    # Successful fetch
    new_value = result.value if cell != "cop" else result.note.split()[0] if result.note else None
    # For cop, the value comes from a tuple result; the dispatcher handles that
    changed = False
    if cell != "cop":
        if result.value is not None and result.value != prior_value:
            model[cell] = result.value
            changed = True
    # cop is handled separately in refresh_model

    prov[cell] = {
        "mode": "auto",
        "source_url": result.source_url,
        "captured_at": result.captured_at,
        "content_hash": result.content_hash,
        "confidence": result.confidence,
        "note": result.note,
        "last_auto_attempt": now_iso(),
    }

    # Mirror source URL into model['urls'] for the dashboard detail panel
    if result.source_url:
        model.setdefault("urls", {})[cell] = result.source_url

    if changed:
        log.info("  %s: %s -> %s (%s)", cell, prior_value, result.value, result.note or "")
    return changed


def refresh_model(model: dict, http: HttpClient, cop_index: CoPSignatoryIndex, audit_dir: Path) -> int:
    """Run all auto fetchers for one model. Returns count of changes."""
    name = model.get("n", "?")
    log.info("refreshing: %s (%s)", name, model.get("p", ""))

    init_provenance(model)
    changes = 0

    # --- mc: model card ---
    prior = model.get("mc")
    res = fetch_model_card(http, model)
    if record_auto(model, "mc", res, prior):
        changes += 1

    # --- td: training data disclosure ---
    prior = model.get("td")
    res = fetch_training_data_disclosure(http, model)
    if record_auto(model, "td", res, prior):
        changes += 1

    # --- cop: code of practice signatory ---
    prior = model.get("cop")
    new_cop, res = fetch_cop_status(cop_index, model)
    if res.error:
        model["_provenance"]["cop"] = {
            "mode": model["_provenance"]["cop"].get("mode", "manual"),
            "last_auto_attempt": now_iso(),
            "last_auto_error": res.error,
            **{k: model["_provenance"]["cop"].get(k) for k in ("source_url", "captured_at", "note")},
        }
        log.info("  cop: fetcher error (%s) — keeping prior %s", res.error, prior)
    else:
        # Preserve manually-set "S" (Safety chapter only) if our auto fetcher says "N"
        # because we can't currently distinguish S from N automatically.
        existing_mode = model["_provenance"]["cop"].get("mode", "manual")
        if prior == "S" and new_cop == "N" and existing_mode == "manual":
            log.info("  cop: keeping manual 'S' (Safety chapter only) over auto 'N'")
            model["_provenance"]["cop"] = {
                "mode": "manual-override",
                "source_url": res.source_url,
                "captured_at": res.captured_at,
                "note": "auto says N, manual override preserves S",
                "last_auto_attempt": now_iso(),
            }
        elif new_cop is not None and new_cop != prior:
            model["cop"] = new_cop
            changes += 1
            log.info("  cop: %s -> %s (%s)", prior, new_cop, res.note or "")
            model["_provenance"]["cop"] = {
                "mode": "auto",
                "source_url": res.source_url,
                "captured_at": res.captured_at,
                "content_hash": res.content_hash,
                "note": res.note,
                "last_auto_attempt": now_iso(),
            }
            if res.source_url:
                model.setdefault("urls", {})["cop"] = res.source_url
        elif new_cop is not None:
            model["_provenance"]["cop"] = {
                "mode": "auto",
                "source_url": res.source_url,
                "captured_at": res.captured_at,
                "content_hash": res.content_hash,
                "note": res.note,
                "last_auto_attempt": now_iso(),
            }
            if res.source_url:
                model.setdefault("urls", {})["cop"] = res.source_url

    # --- vd: vulnerability disclosure (GitHub) ---
    prior = model.get("vd")
    res = fetch_vulnerability_disclosure(http, model)
    if record_auto(model, "vd", res, prior):
        changes += 1

    # last_verified always bumps for the auto-cells set
    model["last_verified"] = today_str()

    if changes > 0:
        audit_dir.mkdir(parents=True, exist_ok=True)
        log_path = audit_dir / f"{name.replace(' ', '_').replace('/', '_')}.jsonl"
        with log_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps({
                "timestamp": now_iso(),
                "changes": changes,
                "provenance_snapshot": {
                    c: model["_provenance"].get(c, {}).get("note") for c in AUTO_FETCHED_CELLS
                },
            }) + "\n")

    return changes


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", default="data/models.json")
    ap.add_argument("--output", default="data/models.json")
    ap.add_argument("--log-dir", default="data/audit")
    ap.add_argument("--limit", type=int, default=0,
                    help="Only refresh the first N models (testing)")
    args = ap.parse_args()

    in_path = Path(args.input)
    out_path = Path(args.output)
    audit_dir = Path(args.log_dir)

    if not in_path.exists():
        log.error("Input file not found: %s", in_path)
        return 1

    payload = json.loads(in_path.read_text(encoding="utf-8"))
    models = payload.get("models", [])
    if args.limit:
        models = models[: args.limit]

    log.info("Refreshing %d models", len(models))

    http = HttpClient(
        hf_token=os.environ.get("HF_TOKEN") or None,
        gh_token=os.environ.get("GH_TOKEN") or None,
    )
    cop_index = CoPSignatoryIndex(http)

    total_changes = 0
    for m in models:
        try:
            total_changes += refresh_model(m, http, cop_index, audit_dir)
        except Exception as e:
            log.exception("refresh_model crashed on %s: %s", m.get("n"), e)

    payload["meta"] = payload.get("meta", {})
    payload["meta"]["generated_at"] = today_str()
    payload["meta"]["generator"] = "collectors/refresh.py"
    payload["meta"]["auto_fetched_cells"] = sorted(AUTO_FETCHED_CELLS)
    payload["meta"]["total_changes_this_run"] = total_changes

    # Write the full set back (not just the limit slice)
    if args.limit:
        full = json.loads(in_path.read_text(encoding="utf-8"))
        # Merge only the refreshed slice
        full["meta"] = payload["meta"]
        for i, m in enumerate(models):
            full["models"][i] = m
        payload = full

    out_path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    log.info("Wrote %s — %d total changes", out_path, total_changes)
    return 0


if __name__ == "__main__":
    sys.exit(main())
