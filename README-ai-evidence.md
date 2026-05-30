# AI Evidence Dashboard — `gkrpro.github.io` integration

Drop-in package that adds an **AI Model Security Evidence Dashboard** to your existing site at `/ai-evidence/`, navigable from your site's top nav and from the "Key Frameworks & Assets" section on the landing page.

Final URL: **`https://gkrpro.github.io/ai-evidence/`**

---

## What's in this package

```
ai-evidence/                              ← NEW subdirectory
  index.html                              ← Dashboard page (with your site's nav bar)
  data/models.json                        ← 64-model seed dataset
  collectors/
    refresh.py                            ← Python collector skeleton
    requirements.txt

.github/workflows/
  ai-evidence-refresh.yml                 ← NEW workflow (namespaced, won't collide
                                              with your existing deploy workflow)

SNIPPET-for-root-index.html               ← Two small edits for your existing index.html
README-ai-evidence.md                     ← This file
```

---

## Installation (4 steps)

### 1. Unzip into your repo root

```bash
git clone https://github.com/gkrpro/gkrpro.github.io.git
cd gkrpro.github.io
git checkout -b add-ai-evidence

unzip ~/Downloads/gkrpro-ai-evidence-drop.zip
```

This creates `ai-evidence/`, adds the workflow to `.github/workflows/`, and drops `SNIPPET-for-root-index.html` and this README at the repo root.

### 2. Edit your existing `index.html` (two small additions)

Open `SNIPPET-for-root-index.html` for the exact paste-ready blocks. In short:

**(a) Add a nav item** — between "Decision Records" and "About":

```html
<a href="/ai-evidence/">AI Evidence</a>
```

**(b) Add a card to "Key Frameworks & Assets"** — alongside your existing entries like "Three-Archetype Governance Model" and "Multi-Cloud Control Mapping":

```html
<div class="framework-card">
  <h4>🛡️ AI Model Security Evidence Dashboard</h4>
  <p>Public transparency tool cataloguing what security-relevant evidence exists per AI model — model cards, system cards, SOC 2, ISO 27001, EU AI Act &amp; GPAI Code of Practice status, DPA, no-training clauses. 60+ frontier and open-weight models. Not a ranking; not a score.</p>
  <p><a href="/ai-evidence/">Open the dashboard →</a></p>
</div>
```

Replace `framework-card` with the actual class name your other cards use, so styling carries over. (I can see your card pattern from the rendered page but not your CSS classes — adjust accordingly.)

### 3. Optional: delete the `SNIPPET-for-root-index.html` file once you've used it

```bash
rm SNIPPET-for-root-index.html
```

### 4. Commit & push

```bash
git add ai-evidence/ .github/workflows/ai-evidence-refresh.yml README-ai-evidence.md index.html
git commit -m "Add AI Model Security Evidence Dashboard at /ai-evidence/"
git push origin add-ai-evidence
```

Open the PR, review, merge. Your existing deploy workflow picks up the new files automatically.

---

## ⚠️ Verify your existing deploy workflow

Since your Pages source is **GitHub Actions**, you already have a deploy workflow in `.github/workflows/`. Open it and confirm:

1. **`actions/upload-pages-artifact` uploads the whole repo** — look for `path: '.'`. If `path:` points to a specific folder, change it to `'.'` or move `ai-evidence/` inside that folder.

2. **Trigger covers the new files** — most deploy workflows use `push: branches: [main]` which covers everything. If yours uses a `paths:` filter, add `ai-evidence/**` and `index.html`.

---

## Visual integration — known limitation

The dashboard page ships with its own clean styling that **won't perfectly match your existing site CSS** because I could see your site's rendered content but not its source CSS classes. Two options:

- **Accept the visual difference** — the dashboard has a sticky top nav linking back to your other pages (Home / Blog / Frameworks / Decision Records / About), and uses a neutral light/dark-mode design. It looks professional, just not identical.
- **Send me your site's CSS** (or paste a representative page like `frameworks.html`) and I'll regenerate `ai-evidence/index.html` matching your actual classes, colors, and typography exactly.

---

## Triggers (after merge)

**Manual:** Repo → Actions → "Refresh AI evidence dataset" → Run workflow. Opens a PR.

**Scheduled:** Mondays 06:00 UTC, direct commit.

**Webhook:**
```bash
curl -X POST \
  -H "Authorization: Bearer $GH_TOKEN" \
  -H "Accept: application/vnd.github+json" \
  https://api.github.com/repos/gkrpro/gkrpro.github.io/dispatches \
  -d '{"event_type": "ai-evidence-refresh", "client_payload": {"reason": "your reason"}}'
```

---

## What's still skeleton

The collector (`ai-evidence/collectors/refresh.py`) is functional but the per-cell fetchers are stubs that preserve prior values. The 64 seed values are illustrative. Implement real fetchers per provider before relying on the data publicly — Hugging Face model-card fetcher is the easiest start; EU AI Office CoP signatory parser is the highest-value.
