# Accounts receivable (QuickBooks → Supabase → Streamlit)

Small pipeline that syncs **QuickBooks** invoices and payments into **Supabase**, and a **Streamlit** dashboard for AR metrics.

## Layout

| Path | Purpose |
|------|---------|
| `src/payments_ar/config.py` | Loads `.env` from the project root; **no secrets in code**. |
| `pipelines/sync_quickbooks_to_supabase.py` | ETL: QuickBooks API → Supabase `invoices` / `payments`. |
| `scripts/quickbooks_oauth_authorization_code.py` | Optional one-time OAuth: authorization code → tokens (save refresh token for sync). |
| `app/dashboard.py` | Streamlit AR dashboard (reads Supabase only). |

## Setup

1. Create a virtual environment and install the project in editable mode:

   ```bash
   cd /path/to/Payments
   python3 -m venv venv
   source venv/bin/activate   # Windows: venv\Scripts\activate
   pip install -e .
   ```

2. **Secrets:** copy `.env.example` to `.env` and fill in values. Never commit `.env` (it is listed in `.gitignore`).

3. **Rotate credentials** that were previously pasted into old scripts or chat logs, then put only the new values in `.env`.

## Commands

- **Sync QuickBooks → Supabase**

  ```bash
  python pipelines/sync_quickbooks_to_supabase.py
  ```

- **Dashboard**

  ```bash
  streamlit run app/dashboard.py
  ```

- **One-time OAuth token exchange** (after setting `QUICKBOOKS_AUTH_CODE` and `QUICKBOOKS_REDIRECT_URI` in `.env`)

  ```bash
  python scripts/quickbooks_oauth_authorization_code.py
  ```

## Environment variables

See `.env.example` for the full list. Required for the sync pipeline: Supabase URL/key and QuickBooks client id/secret, refresh token, realm id. Set `QUICKBOOKS_ENV=production` when you leave the sandbox API.

## Verify before a demo

From the project root (with venv activated):

```bash
pip install -e .
python scripts/verify_setup.py
```

`verify_setup.py` checks that required files exist and that **each variable in `.env` has a non-empty value** (it never prints secret values).

- **Dashboard only:** needs `SUPABASE_URL` and `SUPABASE_SERVICE_KEY`.
- **Full QuickBooks sync:** also needs `QUICKBOOKS_CLIENT_ID`, `QUICKBOOKS_CLIENT_SECRET`, `QUICKBOOKS_REFRESH_TOKEN`, and `QUICKBOOKS_REALM_ID`.

Optional one-liner (syntax + verify):

```bash
bash scripts/run_checks.sh
```

Then run the sync and dashboard (needs network). If `verify_setup.py` fails, fix `.env` locally — credentials are never committed.
