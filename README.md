# QuickBooks → Supabase AR Pipeline

A small Python pipeline that syncs **QuickBooks Online** invoices and payments into **Supabase**, plus a **Streamlit** dashboard for accounts-receivable metrics and charts.

## Overview

| Component | Role |
|-----------|------|
| **Sync** | Fetches invoice and payment data from the QuickBooks API and upserts into Supabase tables (`invoices`, `payments`). |
| **Dashboard** | Read-only Streamlit app that queries Supabase for KPIs, portfolio totals, and per-invoice views. |
| **Config** | Secrets and endpoints load from a root `.env` file; nothing sensitive is hard-coded. |

**Prerequisites:** Python **3.11+**, Supabase project with matching tables, and (for sync) QuickBooks API credentials. See [Environment variables](#environment-variables).

## Quick start

1. **Clone** the repository and enter the project root.

2. **Create a virtual environment** and install the package in editable mode:

   ```bash
   python3 -m venv venv
   source venv/bin/activate          # Windows: venv\Scripts\activate
   pip install -e .
   ```

3. **Configure secrets:** copy `.env.example` to `.env` and fill in values. Do not commit `.env` (it is gitignored).

4. **Verify** (optional but recommended):

   ```bash
   python scripts/verify_setup.py
   ```

   This checks required files, imports, and that expected `.env` keys are present and non-empty (values are never printed).

## Usage

Run these from the **project root** with the virtual environment activated.

| Task | Command |
|------|---------|
| Sync QuickBooks → Supabase | `python pipelines/sync_quickbooks_to_supabase.py` |
| AR dashboard | `streamlit run app/dashboard.py` |
| OAuth token exchange (one-time; see below) | `python scripts/quickbooks_oauth_authorization_code.py` |

**OAuth helper:** set `QUICKBOOKS_AUTH_CODE` and `QUICKBOOKS_REDIRECT_URI` in `.env` as described in `.env.example`, then run the OAuth script to obtain tokens. Store the refresh token securely for ongoing sync.

**Optional checks:** `bash scripts/run_checks.sh` runs syntax compilation and `verify_setup.py`. If `venv/bin/python` is missing, use `VENV_PYTHON=python3 bash scripts/run_checks.sh`.

## Environment variables

The canonical list and comments live in **`.env.example`**. Summary:

| Area | Variables |
|------|-----------|
| Supabase (dashboard + sync target) | `SUPABASE_URL`, `SUPABASE_SERVICE_KEY` |
| QuickBooks API (sync) | `QUICKBOOKS_CLIENT_ID`, `QUICKBOOKS_CLIENT_SECRET`, `QUICKBOOKS_REFRESH_TOKEN`, `QUICKBOOKS_REALM_ID` |
| QuickBooks environment | `QUICKBOOKS_ENV` — `sandbox` or `production` |

Set `QUICKBOOKS_ENV=production` when using the production QuickBooks API (not the sandbox).

**Minimum for dashboard only:** `SUPABASE_URL` and `SUPABASE_SERVICE_KEY`.  
**Full sync:** all variables in the table above.

## Project layout

| Path | Purpose |
|------|---------|
| `src/payments_ar/` | Package code; `config.py` loads `.env` from the project root. |
| `pipelines/sync_quickbooks_to_supabase.py` | ETL: QuickBooks → Supabase. |
| `app/dashboard.py` | Streamlit AR dashboard (Supabase only). |
| `scripts/quickbooks_oauth_authorization_code.py` | Optional OAuth authorization-code flow. |
| `scripts/verify_setup.py` | Local setup and `.env` checks. |
| `scripts/run_checks.sh` | Compile + verify wrapper. |

## Security

- Rotate any credentials that were exposed in old scripts, logs, or chat history; use only current values in `.env`.
- Share secrets through approved channels (password manager, vault, encrypted share)—not in the repo or public issues.

## Demo and handoff

For reviewers or stakeholders: provide the repository (or a zip excluding `.env`) and a short note on purpose—QuickBooks data → Supabase → Streamlit metrics and charts—and the [Usage](#usage) commands. For a live demo, run sync then the dashboard (network required); screenshots work for async review. If `verify_setup.py` fails, fix `.env` locally—credentials are never committed. Reviewers need their own `.env` (or provisioned read-only credentials), Python 3.11+, and network access to Intuit and Supabase.
