"""
One-time helper: exchange a QuickBooks authorization code for tokens.

Set in `.env`:
  QUICKBOOKS_AUTH_CODE
  QUICKBOOKS_REDIRECT_URI  (must match the app redirect URI in Intuit Developer)

Run:

    python scripts/quickbooks_oauth_authorization_code.py

Store the returned refresh token as QUICKBOOKS_REFRESH_TOKEN for the sync pipeline.
"""

from __future__ import annotations

import base64
import json
import sys
from pathlib import Path

import requests

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(_ROOT / "src"))

from payments_ar.config import (  # noqa: E402
    ConfigurationError,
    quickbooks_auth_code,
    quickbooks_client_id,
    quickbooks_client_secret,
    quickbooks_redirect_uri,
)


def main() -> None:
    code = quickbooks_auth_code()
    redirect = quickbooks_redirect_uri()
    if not code or not redirect:
        raise ConfigurationError(
            "Set QUICKBOOKS_AUTH_CODE and QUICKBOOKS_REDIRECT_URI in `.env` for this script."
        )

    url = "https://oauth.platform.intuit.com/oauth2/v1/tokens/bearer"
    cid = quickbooks_client_id()
    secret = quickbooks_client_secret()
    credentials = f"{cid}:{secret}".encode("utf-8")
    auth_header = base64.b64encode(credentials).decode("utf-8")
    headers = {
        "Authorization": f"Basic {auth_header}",
        "Content-Type": "application/x-www-form-urlencoded",
    }
    data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": redirect,
    }
    resp = requests.post(url, headers=headers, data=data, timeout=60)
    resp.raise_for_status()
    print(json.dumps(resp.json(), indent=2))


if __name__ == "__main__":
    try:
        main()
    except ConfigurationError as e:
        print(e, file=sys.stderr)
        sys.exit(1)
