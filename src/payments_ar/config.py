"""Load environment from `.env` (project root) and expose required settings."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

# Project root = parent of `src/`
_PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(_PROJECT_ROOT / ".env")


class ConfigurationError(RuntimeError):
    """Raised when a required secret or setting is missing."""


def _require(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        env_file = _PROJECT_ROOT / ".env"
        raise ConfigurationError(
            f"Missing required environment variable `{name}`. "
            f"Add it to `{env_file}` (see `.env.example`). "
            "For Supabase: Dashboard → Project Settings → API → Project URL and service_role key."
        )
    return value


def project_root() -> Path:
    return _PROJECT_ROOT


# --- Supabase ---


def supabase_url() -> str:
    return _require("SUPABASE_URL")


def supabase_service_key() -> str:
    return _require("SUPABASE_SERVICE_KEY")


# --- QuickBooks ---


def quickbooks_client_id() -> str:
    return _require("QUICKBOOKS_CLIENT_ID")


def quickbooks_client_secret() -> str:
    return _require("QUICKBOOKS_CLIENT_SECRET")


def quickbooks_refresh_token() -> str:
    return _require("QUICKBOOKS_REFRESH_TOKEN")


def quickbooks_realm_id() -> str:
    return _require("QUICKBOOKS_REALM_ID")


def quickbooks_env() -> str:
    return os.getenv("QUICKBOOKS_ENV", "sandbox").strip().lower() or "sandbox"


def quickbooks_query_base_url() -> str:
    realm = quickbooks_realm_id()
    if quickbooks_env() == "production":
        host = "https://quickbooks.api.intuit.com"
    else:
        host = "https://sandbox-quickbooks.api.intuit.com"
    return f"{host}/v3/company/{realm}/query"


# --- Optional: one-time OAuth code exchange ---


def quickbooks_auth_code() -> str | None:
    v = os.getenv("QUICKBOOKS_AUTH_CODE", "").strip()
    return v or None


def quickbooks_redirect_uri() -> str | None:
    v = os.getenv("QUICKBOOKS_REDIRECT_URI", "").strip()
    return v or None
