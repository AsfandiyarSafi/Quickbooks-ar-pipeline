#!/usr/bin/env bash
# Run from project root or via: bash scripts/run_checks.sh
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
: "${VENV_PYTHON:=$ROOT/venv/bin/python}"
if [[ ! -x "$VENV_PYTHON" ]]; then
  echo "Use: VENV_PYTHON=python3 bash scripts/run_checks.sh" >&2
  VENV_PYTHON="${VENV_PYTHON:-python3}"
fi
"$VENV_PYTHON" -m compileall -q src app pipelines scripts
echo "compileall: OK"
"$VENV_PYTHON" scripts/verify_setup.py
