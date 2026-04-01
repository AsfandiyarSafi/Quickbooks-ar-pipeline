#!/usr/bin/env python3
"""
Local checks: package import, required files, and `.env` keys with non-empty values (names only).

Run from project root:
  python scripts/verify_setup.py
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

REQUIRED_FILES = [
    "pyproject.toml",
    "README.md",
    ".env.example",
    "src/payments_ar/config.py",
    "pipelines/sync_quickbooks_to_supabase.py",
    "app/dashboard.py",
]

# Minimum for Streamlit dashboard
DASHBOARD_KEYS = ("SUPABASE_URL", "SUPABASE_SERVICE_KEY")
# Full QuickBooks sync
SYNC_KEYS = DASHBOARD_KEYS + (
    "QUICKBOOKS_CLIENT_ID",
    "QUICKBOOKS_CLIENT_SECRET",
    "QUICKBOOKS_REFRESH_TOKEN",
    "QUICKBOOKS_REALM_ID",
)


def _parse_env_file(raw: str) -> dict[str, str]:
    out: dict[str, str] = {}
    for line in raw.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        k, v = line.split("=", 1)
        k, v = k.strip(), v.strip().strip('"').strip("'")
        if k:
            out[k] = v
    return out


def main() -> int:
    print("Payments AR — setup verification\n")
    bad = False

    for rel in REQUIRED_FILES:
        p = ROOT / rel
        ok = p.is_file()
        print(f"  [{'OK' if ok else '!!'}] {rel}")
        if not ok:
            bad = True

    try:
        import payments_ar.config  # noqa: F401
        print("\n  [OK] import payments_ar.config")
    except Exception as e:
        print(f"\n  [!!] import payments_ar.config: {e}")
        bad = True

    env_path = ROOT / ".env"
    if not env_path.is_file():
        print("\n  [!!] No `.env` file — copy `.env.example` to `.env` and add secrets.")
        return 1

    raw = env_path.read_text(encoding="utf-8", errors="replace")
    env_vals = _parse_env_file(raw)

    def nonempty(name: str) -> bool:
        return bool(env_vals.get(name, "").strip())

    print("\n  Dashboard (Supabase) — non-empty values required:")
    for name in DASHBOARD_KEYS:
        ok = nonempty(name)
        print(f"    [{'OK' if ok else '--'}] {name}")
        if not ok:
            bad = True

    print("\n  QuickBooks sync — non-empty values required for pipeline:")
    qb_keys = SYNC_KEYS[len(DASHBOARD_KEYS) :]
    for name in qb_keys:
        ok = nonempty(name)
        print(f"    [{'OK' if ok else '--'}] {name}")
        if not ok:
            bad = True

    if bad:
        print("\n  Fix missing files or empty variables, then re-run.")
        print("  Dashboard-only: set at least SUPABASE_URL and SUPABASE_SERVICE_KEY.")
        print("  Full sync: also set all QUICKBOOKS_* variables (get refresh token from OAuth).")
        return 1

    print("\n  Structure and `.env` look ready for sync + dashboard.")
    print("  Next: `python pipelines/sync_quickbooks_to_supabase.py`")
    print("        `streamlit run app/dashboard.py`")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
