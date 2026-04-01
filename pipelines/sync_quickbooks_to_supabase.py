"""
Pipeline: fetch invoices and payments from QuickBooks, upsert into Supabase.

Run from project root (after `pip install -e .` and a filled `.env`):

    python pipelines/sync_quickbooks_to_supabase.py
"""

from __future__ import annotations

import base64
import logging
import sys
from pathlib import Path

import requests
from supabase import create_client

# Allow running as `python pipelines/...` without install
_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(_ROOT / "src"))

from payments_ar.config import (  # noqa: E402
    ConfigurationError,
    quickbooks_client_id,
    quickbooks_client_secret,
    quickbooks_query_base_url,
    quickbooks_refresh_token,
    supabase_service_key,
    supabase_url,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s %(message)s",
)
logger = logging.getLogger("sync_quickbooks_to_supabase")


def get_access_token(refresh_token: str) -> tuple[str, str | None]:
    url = "https://oauth.platform.intuit.com/oauth2/v1/tokens/bearer"
    cid = quickbooks_client_id()
    secret = quickbooks_client_secret()
    credentials = f"{cid}:{secret}".encode("utf-8")
    auth_header = base64.b64encode(credentials).decode("utf-8")
    headers = {
        "Authorization": f"Basic {auth_header}",
        "Content-Type": "application/x-www-form-urlencoded",
    }
    data = {"grant_type": "refresh_token", "refresh_token": refresh_token}
    resp = requests.post(url, headers=headers, data=data, timeout=60)
    try:
        resp.raise_for_status()
    except requests.HTTPError as exc:
        body = (resp.text or "")[:500]
        logger.error("OAuth token request failed: %s — %s", exc, body)
        raise
    tokens = resp.json()
    new_refresh = tokens.get("refresh_token")
    return tokens["access_token"], new_refresh


def fetch_qb_data(access_token: str, query: str) -> list:
    headers = {"Authorization": f"Bearer {access_token}", "Accept": "application/json"}
    resp = requests.get(
        quickbooks_query_base_url(),
        headers=headers,
        params={"query": query},
        timeout=120,
    )
    try:
        resp.raise_for_status()
    except requests.HTTPError as exc:
        body = (resp.text or "")[:800]
        logger.error("QuickBooks query failed (%s): %s — %s", query, exc, body)
        raise
    key = query.split()[3]
    return resp.json().get("QueryResponse", {}).get(key, [])


def run() -> None:
    refresh = quickbooks_refresh_token()
    access_token, new_refresh = get_access_token(refresh)
    if new_refresh and new_refresh != refresh:
        logger.warning(
            "QuickBooks returned a new refresh token. Update QUICKBOOKS_REFRESH_TOKEN in `.env`."
        )

    supabase = create_client(supabase_url(), supabase_service_key())

    invoices = fetch_qb_data(access_token, "select * from Invoice")
    payments = fetch_qb_data(access_token, "select * from Payment")
    logger.info("Fetched %s invoices and %s payments.", len(invoices), len(payments))

    for inv in invoices:
        supabase.table("invoices").upsert(
            {
                "id": inv.get("Id"),
                "customername": inv.get("CustomerRef", {}).get("name"),
                "invoicenumber": inv.get("DocNumber"),
                "totalamt": inv.get("TotalAmt"),
                "balance": inv.get("Balance"),
                "txndate": inv.get("TxnDate"),
                "status": "Paid" if inv.get("Balance") == 0 else "Open",
            }
        ).execute()

    for pay in payments:
        supabase.table("payments").upsert(
            {
                "id": pay.get("Id"),
                "invoice_id": pay.get("InvoiceRef", {}).get("value"),
                "customername": pay.get("CustomerRef", {}).get("name"),
                "totalamt": pay.get("TotalAmt"),
                "paymentdate": pay.get("TxnDate"),
                "paymentmethod": pay.get("PaymentMethodRef", {}).get("name"),
            }
        ).execute()

    logger.info("QuickBooks → Supabase sync finished.")


if __name__ == "__main__":
    try:
        run()
    except ConfigurationError as e:
        logger.error("%s", e)
        sys.exit(1)
    except (requests.RequestException, OSError) as e:
        logger.error("Network or API error: %s", e)
        sys.exit(1)
